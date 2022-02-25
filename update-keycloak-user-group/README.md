# Update Keycloak User Group
This script is used to add users to the judgment group in Keycloak.

## Running the script
There are two environment variables
* `ENVIRONMENT` - This is used to build the url for Keycloak so needs to be either, integration, staging or empty string.
* `AUTH_SECRET` - This is the secret for the tdr-user-admin-client

There is a file called `emails.txt` in `src/main/resources` 

Add the email addresses you want to update into that file and run the script with `sbt run`
