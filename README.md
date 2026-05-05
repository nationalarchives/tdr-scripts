## TDR Scripts

This is a repository for scripts which are run infrequently and don't belong with other projects.
Terraform scripts are put into separate directories inside the terraform directories. Other non-terraform scripts are kept in their own directory at the root of the project.

### Keycloak Sandbox

Terraform script for creating a temporary Keycloak instance in the Sandbox
environment. This instance does not have all of the security protections used
in the integration/staging/production version of Keycloak, so it should only be
used for testing new Keycloak configuration.

See the [Keycloak Sandbox Readme](keycloak-sandbox) for setup instructions.

[keycloak-sandbox]: terraform/keycloak-sandbox/README.md

### ECR Sandbox

Terraform script for creating a temporary Elastic Container Registry with image
scanning in the Sandbox account. This is useful for testing the image scanning
results of Docker image upgrades.

See the [ECR Sandbox Readme](ecr-sandbox) for setup instructions.

[ecr-sandbox]: terraform/ecr-sandbox/README.md

### Generate Release Versions

This is a python script which is run on GitHub. It generates an html file and a Slack message which show which repositories have out of date versions deployed to the staging and production environments. It does this by looking at the release tags on each of the `release-$environment` branches.

#### Running on GitHub
The GitHub action to run the script is [here](https://github.com/nationalarchives/tdr-scripts/blob/master/.github/workflows/generate.yml) and when the action is run, it generates [an html file](https://nationalarchives.github.io/tdr-scripts/transfer-digital-records/output.html) like this one. 

##### Running locally
There is only one dependency outside the standard python library which will need to be installed to run this locally. You can install this system wide by running `pip install quik` but it's better to use a virtual environment.
You will need to use Python 3. 
For the Slack url environment variable, you can set it to a real Slack webhook url if you want to send messages to Slack or leave it unset and it will print the Slack message json to console.

```bash
cd release-versions
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export GITHUB_API_TOKEN=valid_api_token
python generate_release_file.py
```

This will print the slack json to the console and generate an output.html file which you can view in a browser. The css comes from Jenkins and gives a 403 error when you try to load it from a local file. If you want to view it with the css, you can replace the `href` in the `<link>` tag in `output.html` to the bootstrap css file `https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/css/bootstrap.min.css`

#### Cleaning up
```bash
deactivate
rm -r venv
```

### Judgment Report Generator
This will generate a csv report of all judgment consignments for the given environment.

#### Setting up the environment
```bash
cd judgment-report
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Running the report
This report needs AWS credentials with SSM access to work.
These can be set with environment variables, in `~/.aws/credentials` or using sso profiles.

Once these are set you can run: 

`python report.py environment_name email_address_1 email_address_2`

It will create a file called `report.csv` in the same directory and will send a slack message with the file to all of the email addresses provided as arguments. You can provide zero or more email addresses.

#### Cleaning up
```bash
deactivate
rm -r venv
```
