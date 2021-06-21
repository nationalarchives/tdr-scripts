from quik import FileLoader
from collections import ChainMap
import requests
import os

releases = []

headers = {'Content-Type': 'application/json',
                              'Authorization': f'Bearer {os.environ["GITHUB_API_TOKEN"]}'}


def url(repo, suffix):
    return f"https://api.github.com/repos/nationalarchives/{repo}/{suffix}"


def get_versions(repository_name):
    branches = requests.get(url(repository_name, "branches"), headers = headers).json()
    filtered_release_branches = dict(ChainMap(*[{branch["name"]: branch} for branch in branches if
                                                branch["name"] in ["release-intg", "release-staging", "release-prod"]]))

    print(filtered_release_branches)
    if len(filtered_release_branches) > 0:
        tags = requests.get(url(repo, "tags"), headers = headers).json()
        intg_version = get_version_for_stage(tags, filtered_release_branches["release-intg"])
        staging_version = get_version_for_stage(tags, filtered_release_branches["release-staging"])
        prod_version = get_version_for_stage(tags, filtered_release_branches["release-prod"])
        return {"repository": repository_name, "intg_version": intg_version, "staging_version": staging_version,
                "prod_version": prod_version}


def get_version_for_stage(tags, release_branch):
    release_sha = release_branch["commit"]["sha"]
    filtered_release_tags = [tag for tag in tags if tag["commit"]["sha"] == release_sha]
    if len(filtered_release_tags) > 0:
        return filtered_release_tags[0]["name"]
    else:
        return ""


loader = FileLoader(".")
template = loader.load_template('index.html')
repos = requests.get("https://api.github.com/orgs/nationalarchives/teams/transfer-digital-records/repos?per_page=100",
                     headers=headers).json()
filtered_repos = [repo["name"] for repo in repos if not repo["archived"] and not repo["disabled"]]

for repo in filtered_repos:
    versions = get_versions(repo)
    if versions is not None:
        releases.append(versions)
with open("output.html", "w") as output:
    output.write(template.render({'releases': releases}, loader=loader))
