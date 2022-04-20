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

    branches = requests.get(url(repository_name, "branches?per_page=100"), headers=headers).json()
    # If there are no branches found for a repository, you get a message field so we can just ignore those.
    filtered_release_branches = dict(ChainMap(*[{branch["name"]: branch} for branch in branches if
                                                branch["name"] in ["release-intg", "release-staging",
                                                                   "release-prod"]]))

    if len(filtered_release_branches) > 0:
        tags = requests.get(url(repository_name, "tags"), headers=headers).json()

        intg_branch = release_branch(repository_name, "intg", filtered_release_branches, tags)
        staging_branch = release_branch(repository_name, "staging", filtered_release_branches, tags)
        prod_branch = release_branch(repository_name, "prod", filtered_release_branches, tags)

        defined_versions = [branch["version"] for branch in [intg_branch, staging_branch, prod_branch] if branch]
        max_version = max(defined_versions)

        return {
            "repository": repository_name,
            "integration": integration_view_model(intg_branch, max_version),
            "staging": higher_environment_branch_view_model(staging_branch, intg_branch, max_version),
            "production": higher_environment_branch_view_model(prod_branch, staging_branch, max_version),
        }


def release_branch(repo_name, environment, filtered_release_branches, repo_tags):
    branch = filtered_release_branches.get(f"release-{environment}")

    if branch:
        sha = branch["commit"]["sha"] if branch else None
        version = get_version_for_stage(repo_tags, sha) if branch else None
        date = get_date_for_stage(repo_name, sha) if branch else None

        return {
            "environment": environment,
            "version": version,
            "date": date
        }
    else:
        return None


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


def integration_view_model(branch, max_version):
    if branch:
        is_out_of_date = branch["version"] != max_version
        return branch_view_model(is_out_of_date, branch["version"], "")
    else:
        return empty_branch_view_model()


def higher_environment_branch_view_model(branch, lower_environment_branch, max_version):
    if branch:
        is_out_of_date = branch["version"] != max_version if branch else True

        if lower_environment_branch:
            difference_days = (lower_environment_branch["date"] - branch["date"]).days
            lower_branch_name = lower_environment_branch["environment"]
            out_of_date_text = f"({difference_days} day{'' if difference_days == 1 else 's'} behind {lower_branch_name})" if is_out_of_date else ""
        else:
            out_of_date_text = ""

        return branch_view_model(is_out_of_date, branch["version"], out_of_date_text)
    else:
        return empty_branch_view_model()


def empty_branch_view_model():
    return branch_view_model(True, "Unknown", "")


def branch_view_model(is_out_of_date, version, out_of_date_text):
    return {
        "version": version,
        "data_class": "table-danger fw-bold" if is_out_of_date else "table-success",
        "out_of_date": is_out_of_date,
        "date_diff": out_of_date_text
    }


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
        #show first three only to ensure Slack message is not too large so it fails to send
        first_three_out_of_date_releases = out_of_date_releases[:3]
        slack_message = {"blocks": []}

        append_section(slack_message, "Repositories have out of date versions")
        slack_message["blocks"].append({"type": "divider"})

        for out_of_date_release in first_three_out_of_date_releases:
            append_header(slack_message, out_of_date_release["repository"])
            add_stage_info(slack_message, out_of_date_release, "integration")
            add_stage_info(slack_message, out_of_date_release, "staging")
            add_stage_info(slack_message, out_of_date_release, "production")
            slack_message["blocks"].append({"type": "divider"})

        if len(out_of_date_releases) > 3:
            append_section(slack_message, "... further repositories are out of date ...")
            slack_message["blocks"].append({"type": "divider"})

        append_section(slack_message, f"For full list see here: <https://nationalarchives.github.io/tdr-scripts/output.html|Click for the report>")
        if "SLACK_URL" in os.environ:
            requests.post(os.environ["SLACK_URL"], json=slack_message)
        else:
            print(json.dumps(slack_message))


create_html_summary()
send_slack_message()
