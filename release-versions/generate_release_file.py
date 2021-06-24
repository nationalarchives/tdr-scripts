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
    branches = requests.get(url(repository_name, "branches"), headers=headers).json()
    if "message" not in branches:
        filtered_release_branches = dict(ChainMap(*[{branch["name"]: branch} for branch in branches if
                                                    branch["name"] in ["release-intg", "release-staging",
                                                                       "release-prod"]]))

        if len(filtered_release_branches) > 0:
            tags = requests.get(url(repo, "tags"), headers=headers).json()
            intg_version = get_version_for_stage(tags, filtered_release_branches["release-intg"])
            staging_version = get_version_for_stage(tags, filtered_release_branches["release-staging"])
            prod_version = get_version_for_stage(tags, filtered_release_branches["release-prod"])
            max_version = max([intg_version, staging_version, prod_version])

            return {"repository": repository_name,
                    "integration": {"version": intg_version,
                                    "data_class":
                                        "table-success" if intg_version == max_version else "table-danger fw-bold",
                                    "out_of_date": intg_version != max_version
                                    },
                    "staging": {"version": staging_version,
                                "data_class":
                                    "table-success" if staging_version == max_version else "table-danger fw-bold",
                                "out_of_date": staging_version != max_version
                                },
                    "production": {"version": prod_version,
                                   "data_class":
                                       "table-success" if prod_version == max_version else "table-danger fw-bold",
                                   "out_of_date": prod_version != max_version
                                   },
                    }


def get_version_for_stage(tags, release_branch):
    release_sha = release_branch["commit"]["sha"]
    filtered_release_tags = [tag for tag in tags if tag["commit"]["sha"] == release_sha]
    if len(filtered_release_tags) > 0:
        return filtered_release_tags[0]["name"]
    else:
        return ""


def append_section(message, text):
    message["blocks"].append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": text
        }
    })


def append_header(message, text):
    message["blocks"].append(
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": text,
                "emoji": True
            }
        }
    )


def add_stage_info(message, stage):
    append_section(message, f"{stage.title()} version {out_of_date_release[stage]['version']}")


loader = FileLoader(".")
template = loader.load_template('index.html')
repos = requests.get("https://api.github.com/orgs/nationalarchives/teams/transfer-digital-records/repos?per_page=100",
                     headers=headers).json()
filtered_repos = sorted([repo["name"] for repo in repos if not repo["archived"] and not repo["disabled"]])

for repo in filtered_repos:
    versions = get_versions(repo)
    if versions is not None:
        releases.append(versions)
with open("output.html", "w") as output:
    output.write(template.render({'host': os.environ["HOST"], 'releases': releases}, loader=loader))

slack_message = {"blocks": []}

append_section(slack_message, "The following repositories have out of date versions")
slack_message["blocks"].append({"type": "divider"})

out_of_date_releases = [release for release in releases if
                        release["staging"]["out_of_date"] or release["production"]["out_of_date"]]
for out_of_date_release in out_of_date_releases:
    append_header(slack_message, out_of_date_release["repository"])
    add_stage_info(slack_message, "integration")
    add_stage_info(slack_message, "staging")
    add_stage_info(slack_message, "production")
    slack_message["blocks"].append({"type": "divider"})

append_section(slack_message, f"<{os.environ['BUILD_URL']}Release_20Version_20Report/|Click for the report>")

requests.post(os.environ["SLACK_URL"], json=slack_message)
