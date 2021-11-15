# Merge dependabot updates

## Running the script
Install requests globally

`pip install requests`

Go the the directory of the repository you want to merge the dependabot PRs for and run 
```bash
export GITHUB_TOKEN=mygithubtoken
/path/to/tdr-scripts/dependabot-merge/merge.py
```


This will:
* Get all the PRs for a the repository.
* Filter the ones which were raised by dependabot
* Filter the ones with passing status checks.
* Get the package.json changes from each PR.
* Write all of these changes to a new package.json
* Update the package-lock.json
* Create a new branch and commit and push the changes.
* Create a PR for the new branch.