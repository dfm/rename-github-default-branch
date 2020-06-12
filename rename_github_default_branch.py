#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import logging
from typing import Optional, List

import tqdm
import click
import requests

from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    __version__ = None

logger = logging.getLogger(__name__)


GITHUB_API_URL = "https://api.github.com"


def match_repo_name(patterns: List[str], name: str) -> bool:
    return len(patterns) == 0 or any(p.search(name) for p in patterns)


def list_repos(
    session: requests.Session, current: str, patterns: List[str],
) -> List[str]:
    patterns = [re.compile(p, re.I) for p in patterns]
    params = {} if patterns else {"affiliation": "owner"}

    r = session.get(GITHUB_API_URL + "/user/repos", params=params)
    r.raise_for_status()

    # Deal with pagination
    repos = []
    while True:
        repos += [
            repo["full_name"]
            for repo in r.json()
            if not repo["fork"]
            and match_repo_name(patterns, repo["full_name"])
        ]

        if "next" not in r.links:
            break
        url = r.links["next"]["url"]
        r = session.get(url)
        r.raise_for_status()

    return repos


def rename_default_branch(
    session: requests.Session,
    repo_name: str,
    current: str,
    target: str,
    delete_current: bool = False,
) -> None:
    # First, look up the SHA for the current default branch
    r = session.get(
        GITHUB_API_URL + f"/repos/{repo_name}/git/refs/heads/{current}"
    )
    if r.status_code == 404:
        logger.info(f"no branch named {current} on {repo_name}")
        return
    r.raise_for_status()
    sha = r.json()["object"]["sha"]

    # Try to create a new branch with the name given by target
    r = session.post(
        GITHUB_API_URL + f"/repos/{repo_name}/git/refs",
        json={"ref": f"refs/heads/{target}", "sha": sha},
    )
    if r.status_code == 422:
        logger.info(f"branch {target} already exists on {repo_name}")

        # If this branch, make sure that it has the right
        r = session.get(
            GITHUB_API_URL + f"/repos/{repo_name}/git/refs/heads/{target}"
        )
        r.raise_for_status()
        if r.json()["object"]["sha"] != sha:
            logger.warning(
                f"the SHA of branch {target} on {repo_name} does not match "
                f"{current}"
            )
            return

    else:
        r.raise_for_status()

    # Rename the default branch
    r = session.patch(
        GITHUB_API_URL + f"/repos/{repo_name}",
        json={"name": repo_name.split("/")[1], "default_branch": target},
    )
    r.raise_for_status()

    # Delete the existing branch if requested
    if delete_current:
        r = session.delete(
            GITHUB_API_URL + f"/repos/{repo_name}/git/refs/heads/{current}"
        )
        r.raise_for_status()


@click.command()
@click.option(
    "--token", help="A personal access token for this user", type=str
)
@click.option(
    "--current",
    "-c",
    help="The current default branch name to change",
    type=str,
    default="master",
)
@click.option(
    "--target",
    "-t",
    help="The new default branch name to use",
    type=str,
    default="main",
)
@click.option(
    "--repo",
    "-r",
    help="The name of a specific repository",
    multiple=True,
    type=str,
)
@click.option(
    "--pattern",
    "-p",
    help="A regular expression to match against the repository name",
    multiple=True,
    type=str,
)
@click.option(
    "--delete",
    "-d",
    help="Should the current default branch be deleted?",
    is_flag=True,
)
@click.option("--version", help="Print the version number", is_flag=True)
def _main(
    token: Optional[str],
    current: str,
    target: str,
    repo: List[str],
    pattern: List[str],
    delete: bool,
    version: bool,
) -> None:

    if version:
        print(f"rename-github-default-branch v{__version__}")
        return 0

    if not token:
        print(
            "A GitHub.com personal access token must be provided either via "
            "the environment variable 'RENAME_GITHUB_TOKEN' or the command "
            "line flag '--token'"
        )
        return 1

    with requests.Session() as session:
        session.headers.update(
            {
                "Authorization": f"token {token}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github.v3+json",
            }
        )

        if not repo:
            repo = list_repos(session, current, pattern)

        with tqdm.tqdm(total=len(repo)) as bar:
            for r in repo:
                bar.set_description_str(r)
                rename_default_branch(
                    session, r, current, target, delete_current=delete
                )
                bar.update()

    return 0


def main():
    return _main(auto_envvar_prefix="RENAME_GITHUB")


if __name__ == "__main__":
    sys.exit(_main(auto_envvar_prefix="RENAME_GITHUB"))
