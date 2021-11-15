#! /usr/bin/python
import requests
import subprocess
import os
import json

headers = {'Authorization': 'bearer ' + os.environ["GITHUB_TOKEN"]}
working_directory = os.getcwd()
repo_name_process = subprocess.run(f"basename {working_directory}", shell=True, capture_output=True)
repo_name = repo_name_process.stdout.decode("utf-8").strip()
url = f"https://api.github.com/repos/nationalarchives/{repo_name}/pulls"


def status_checks_ok(pr):
    statuses = requests.get(pr["statuses_url"], headers=headers).json()
    return statuses[0]["state"] == "success"


def pr_filter(pr):
    return pr["user"]["login"] == "dependabot[bot]" and status_checks_ok(pr)


pull_requests = requests.get(url, headers=headers).json()
dependabot_prs = [pr for pr in pull_requests if pr_filter(pr)]
version_updates = []
for dependabot_pr in dependabot_prs:
    sha = dependabot_pr["head"]["sha"]
    a = subprocess.run(f"git diff master..{sha} -- npm/package.json",
                       cwd=working_directory, capture_output=True, shell=True)
    lines = a.stdout.decode("utf-8").split("\n")
    line = [x for x in lines if x.startswith("+ ")]
    dependency_updates = line[0].split()
    dependency_name = dependency_updates[1].replace('"', '').replace(":", "")
    dependency_version = dependency_updates[2].replace('"', '').replace(",", "")
    version_updates.append({"name": dependency_name, "version": dependency_version})

with open(working_directory + '/npm/package.json', 'r') as reader:
    package_json = json.loads(reader.read())
    for update in version_updates:
        if update["name"] in package_json["dependencies"]:
            package_json["dependencies"][update["name"]] = update["version"]
        if update["name"] in package_json["devDependencies"]:
            package_json["devDependencies"][update["name"]] = update["version"]

with open(working_directory + '/npm/package.json', 'w') as writer:
    writer.write(json.dumps(package_json, indent=2) + "\n")

subprocess.run("npm i -package-lock-only", cwd=working_directory + "/npm", shell=True)
subprocess.run("git checkout -b dependabot-merged-changes", cwd=working_directory + "/npm", shell=True)
subprocess.run("git add -A", cwd=working_directory + "/npm", shell=True)
subprocess.run("git commit -m 'Merged dependabot changes'", cwd=working_directory + "/npm", shell=True)
subprocess.run("git push -u origin dependabot-merged-changes", cwd=working_directory + "/npm", shell=True)
pr_json = {"head": "dependabot-merged-changes", "base": "master", "title": "Merged dependabot updates"}
res = requests.post(url, json=pr_json, headers=headers)
