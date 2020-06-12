The default git/GitHub branch name [is oppressive terminology](https://tools.ietf.org/id/draft-knodel-terminology-00.html#rfc.section.1.1) ([more info](https://mail.gnome.org/archives/desktop-devel-list/2019-May/msg00066.html)).
It is easy to change the branch name [for a single repository](https://www.hanselman.com/blog/EasilyRenameYourGitDefaultBranchFromMasterToMain.aspx) or [for new repositories](https://leigh.net.au/writing/git-init-main/).
This script makes it easy to rename your default branch on GitHub repositories in bulk.

## Usage

To install, run

```bash
python -m pip install rename-github-default-branch
```

Then, create a [GitHub.com personal access token](https://github.com/settings/tokens) with the `repo` permission scope and set the environment variable:

```bash
export RENAME_GITHUB_TOKEN=YOUR_PERSONAL_ACCESS_TOKEN
```

Then to rename the default branch to `main` for a specific repository (you must have write access):

```bash
rename-github-default-branch -r dfm/rename-github-default-branch -t main
```

Or for all the repos that you own (excluding forks):

```bash
rename-github-default-branch -t main
```

You can also provide regular expressions to match against the repository name. For example:

```bash
rename-github-default-branch -t main -p dfm/* -p exoplanet-dev/*
```
