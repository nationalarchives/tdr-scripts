# Restore a database

This script creates a replica of an existing rds database from a snapshot. It also updates the database url parameter in the parameter store to point to the new database instance.

This script is intended to be used to recover lost data in an emergency if it has been accidentally deleted, or major problem has affected the main database.

Any changes that affect the production database should be made by two people, either sitting together or screen sharing. This is to help prevent mistakes and for accountability.

## Create the replica
`export TF_VAR_database=consignment-api` or `export TF_VAR_database=keycloak`

Set a helper variable as some fields need `consignmentapi` and some need `consignment-api`

`export DB_NO_DASH=$(echo $TF_VAR_database | sed  's/-//g')`

## Run terraform

**Important Note**: restore-database uses v1.5.0 of Terraform. Ensure that Terraform v1.5.0 is installed before proceeding.

```
export TF_VAR_tdr_account_number=xxxxxxxxxxx
export TF_VAR_instance_identifier=$(aws rds describe-db-instances --query="DBInstances[?DBName=='$DB_NO_DASH'].DBInstanceIdentifier" --output text)
export TF_VAR_engine_version=$(aws rds describe-db-instances --query="DBInstances[?DBName=='$DB_NO_DASH'].EngineVersion" --output text)
export TF_VAR_restore_time=YYYY-MM-DD-HH-MM # optional if want to restore DB to a point in time instead of latest possible version
export PROFILE=intg # replace with staging or prod if using those environments

terraform init
terraform workspace new intg # replace with staging or prod if using those environments
terraform apply
```

The restore may take 10-15 minutes depending on the size of the database when you run this. Terraform won't exit until the instance is created.

## Restart the service to pick up the new database
This only needs to be run if you want to switch the API over to the new database instance. If you're only planning to manually move the SQL over from the new instance then this step can be skipped.
```
aws ecs update-service --service $DB_NO_DASH_service_$PROFILE --cluster $DB_NO_DASH_$PROFILE --force-new-deployment
```

## Copy parts of the data from one instance to another.
If you want to manually copy parts of the data from the old instance to the new one, you will need to [create a bastion](https://github.com/nationalarchives/tdr-scripts/actions/workflows/bastion_deploy.yml) and do this manually.

## Revert the changes
This will need to be done whether or not you've switched the ECS service to the new instance

You need to run the [environments terraform](https://github.com/nationalarchives/tdr-terraform-environments) against the same environment. This will revert the change this terraform project has made to the database/url parameter and update the ECS service which forces a restart. Once this is done and the load balancer has switched to the new task, then run: 
```
terraform state rm aws_ssm_parameter.database_url # Stops terraform trying to delete the datbase url parameter.
terraform destroy
```
