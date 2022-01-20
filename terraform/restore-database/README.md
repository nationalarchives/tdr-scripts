# Restore a database

This script creates a replica of an existing rds database from a snapshot. It also updates the database url parameter in the parameter store to point to the new database cluster.

This script is intended to be used to recover lost data in an emergency if it has been accidentally deleted, or major problem has affected the main database.

Any changes that affect the production database should be made by two people, either sitting together or screen sharing. This is to help prevent mistakes and for accountability.

## Create the replica
`export TF_VAR_database=consignment-api` or `export TF_VAR_database=keycloak`

Set a helper variable as some fields need `consignmentapi` and some need `consignment-api`

`export DB_NO_DASH=$(echo $TF_VAR_database | sed  's/-//g')`

If you want to restore to a particular point in time instead of from the most recent snapshot you can set the `TF_VAR_restore_time` environment variable to a date and time in UTC format. To get the earliest and latest available times

```
aws rds describe-db-clusters --query="DBClusters[?DatabaseName=='$DB_NO_DASH'].[LatestRestorableTime, EarliestRestorableTime]" --output table
```

## Run terraform

**Important Note**: restore-database uses v1.1.3 of Terraform. Ensure that Terraform v1.1.3 is installed before proceeding.

```
export TF_VAR_tdr_account_number=xxxxxxxxxxx
export TF_VAR_cluster_identifier=$(aws rds describe-db-clusters --query="DBClusters[?DatabaseName=='$DB_NO_DASH'].DBClusterIdentifier" --output text)
export TF_VAR_engine_version=$(aws rds describe-db-clusters --query="DBClusters[?DatabaseName=='$DB_NO_DASH'].EngineVersion" --output text)
export PROFILE=intg # replace with staging or prod if using those environments

terraform init
terraform apply
```

The restore may take 10-15 minutes depending on the size of the database when you run this. Terraform won't exit until the cluster is created.

## Restart the service to pick up the new database
This only needs to be run if you want to switch the API over to the new database cluster. If you're only planning to manually move the SQL over from the new cluster then this step can be skipped.
```
aws ecs update-service --service $DB_NO_DASH_service_$PROFILE --cluster $DB_NO_DASH_$PROFILE --force-new-deployment
```

## Copy parts of the data from one cluster to another.
If you don't want to move the API over to point to the new cluster dump sql statements from the new cluster to the existing one, then you'll need to create a bastion host to allow you to connect to both databases. This is a manual process for now. The steps will roughly be:
* Create an EC2 instance in the correct VPC
* For the consignment API, create a role. Attach the `TDRConsignmentApiAllowIAMAuthPolicy${environment}`, `RestoredDbAccessPolicy${environment}` and `AmazonSSMManagedInstanceCore` policies. For the keycloak DB, this isn't needed as it doesn't use IAM authentication. Then create another role with a policy with permissions to assume the first new role and attach this to the EC2 instance. 
* Attach the security group for the ECS task to the EC2 instance.
* Connect to the EC2 instance. Then either connect to the database using IAM auth using a script similar to [the one for the bastion](https://github.com/nationalarchives/tdr-terraform-modules/blob/master/ec2/templates/user_data_postgres.sh.tpl) or connect using psql and the admin keycloak db credentials from the parameter store.

## Revert the changes
This will need to be done whether or not you've switched the ECS service to the new cluster

You need to run the [environments terraform](https://github.com/nationalarchives/tdr-terraform-environments) against the same environment. This will revert the change this terraform project has made to the database/url parameter and update the ECS service which forces a restart. Once this is done and the load balancer has switched to the new task, then run: 
```
terraform state rm aws_ssm_parameter.database_url # Stops terraform trying to delete the datbase url parameter.
terraform destroy
```
