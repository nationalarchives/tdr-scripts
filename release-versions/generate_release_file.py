from quik import FileLoader
from collections import ChainMap
import requests
import os
from datetime import datetime
import json

releases = []

headers = {'Content-Type': 'application/json',
           'Authorization': f'Bearer {os.environ["GITHUB_API_TOKEN"]}'}


def url(repo, suffix):
    return f"https://api.github.com/repos/nationalarchives/{repo}/{suffix}"


def get_versions(repository_name):
    print(f"Fetching release branches for {repository_name}")

    branches = requests.get(url(repository_name, "branches"), headers=headers).json()
    # If there are no branches found for a repository, you get a message field so we can just ignore those.
    filtered_release_branches = dict(ChainMap(*[{branch["name"]: branch} for branch in branches if
                                                branch["name"] in ["release-intg", "release-staging",
                                                                   "release-prod"]]))

    if len(filtered_release_branches) > 0:
        tags = requests.get(url(repository_name, "tags"), headers=headers).json()

        intg_branch = filtered_release_branches.get("release-intg")
        staging_branch = filtered_release_branches.get("release-staging")
        prod_branch = filtered_release_branches.get("release-prod")

        intg_sha = intg_branch["commit"]["sha"] if intg_branch else None
        staging_sha = staging_branch["commit"]["sha"] if staging_branch else None
        prod_sha = prod_branch["commit"]["sha"] if prod_branch else None

        intg_version = get_version_for_stage(tags, intg_sha) if intg_branch else None
        staging_version = get_version_for_stage(tags, staging_sha) if staging_branch else None
        prod_version = get_version_for_stage(tags, prod_sha) if prod_branch else None

        intg_date = get_date_for_stage(repository_name, intg_sha) if intg_branch else None
        staging_date = get_date_for_stage(repository_name, staging_sha) if staging_branch else None
        prod_date = get_date_for_stage(repository_name, prod_sha) if prod_branch else None

        defined_branches = filter(None, [intg_version, staging_version, prod_version])
        max_version = max(defined_branches)

        staging_out_of_date = staging_version != max_version
        prod_out_of_date = prod_version != max_version

        # TODO: Handle intg but no staging, etc.
        if (staging_branch):
            staging_diff = (intg_date - staging_date).days
            staging_diff_text = f"({staging_diff} day{'' if staging_diff == 1 else 's'} behind integration)" if staging_out_of_date else ""
        else:
            staging_diff_text = ""

        if (prod_branch):
            prod_diff = (staging_date - prod_date).days
            prod_diff_text = f"({prod_diff} day{'' if prod_diff == 1 else 's'} behind staging)" if prod_out_of_date else ""
        else:
            prod_diff_text = ""

        return {"repository": repository_name,
                "integration": {"version": intg_version if intg_version else "Unknown",
                                "data_class":
                                    "table-success" if intg_version == max_version else "table-danger fw-bold",
                                "out_of_date": intg_version != max_version,
                                "date_diff": ""
                                },
                "staging": {"version": staging_version if staging_version else "Unknown",
                            "data_class":
                                "table-success" if staging_version == max_version else "table-danger fw-bold",
                            "out_of_date": staging_out_of_date,
                            "date_diff": staging_diff_text
                            },
                "production": {"version": prod_version if prod_version else "Unknown",
                               "data_class":
                                   "table-success" if prod_version == max_version else "table-danger fw-bold",
                               "out_of_date": prod_out_of_date,
                               "date_diff": prod_diff_text
                               },
                }

def get_date_for_stage(repo_name, release_sha):
    commit_response = requests.get(f"{url(repo_name, 'commits')}/{release_sha}", headers=headers).json()
    date_string = commit_response["commit"]["author"]["date"]
    return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")


def get_version_for_stage(tags, release_sha):
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


def add_stage_info(message, release, stage):
    append_section(message, f"{release[stage]['version']} {stage.title()} version {release[stage]['date_diff']}")


def create_html_summary():
    loader = FileLoader(".")
    template = loader.load_template('index.html')
    repos = requests.get(
        "https://api.github.com/orgs/nationalarchives/teams/transfer-digital-records/repos?per_page=100",
        headers=headers).json()
    filtered_repos = sorted([repo["name"] for repo in repos if not repo["archived"] and not repo["disabled"]])

    for repo in filtered_repos:
        versions = get_versions(repo)
        if versions is not None:
            releases.append(versions)
    with open("output.html", "w") as output:
        output.write(template.render({'releases': releases}, loader=loader))


def send_slack_message():
    out_of_date_releases = [release for release in releases if
                            release["staging"]["out_of_date"] or release["production"]["out_of_date"]]

    if len(out_of_date_releases) > 0:
        slack_message = {"blocks": []}

        append_section(slack_message, "The following repositories have out of date versions")
        slack_message["blocks"].append({"type": "divider"})

        for out_of_date_release in out_of_date_releases:
            append_header(slack_message, out_of_date_release["repository"])
            add_stage_info(slack_message, out_of_date_release, "integration")
            add_stage_info(slack_message, out_of_date_release, "staging")
            add_stage_info(slack_message, out_of_date_release, "production")
            slack_message["blocks"].append({"type": "divider"})

        append_section(slack_message, f"<{os.getenv('BUILD_URL', 'h')}Release_20Version_20Report/|Click for the report>")
        if "SLACK_URL" in os.environ:
            requests.post(os.environ["SLACK_URL"], json=slack_message)
        else:
            print(json.dumps(slack_message))


create_html_summary()
send_slack_message()
