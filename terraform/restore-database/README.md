# Restore a database

This script creates a replica of an existing rds database from a snapshot. It also updates the database url parameter in the parameter store to point to the new   

## Create the replica
`export TF_VAR_database=consignment-api` or `export TF_VAR_database=keycloak`


```
export TF_VAR_tdr_account_number=xxxxxxxxxxx
export DB_NO_DASH=$(echo $TF_VAR_database | sed  's/-//g')
export TF_VAR_cluster_identifier=$(aws rds describe-db-clusters --query="DBClusters[?DatabaseName=='$DB_NO_DASH'].DBClusterIdentifier" --output text)
export PROFILE=intg # replace with staging or prod if using those environments

terraform init
terraform apply
```

## Restart the service to pick up the new database
```
aws ecs update-service --service $DB_NO_DASH_service_$PROFILE --cluster $DB_NO_DASH_$PROFILE --force-new-deployment
```

## Revert the changes

You need to run the [environments terraform](https://github.com/nationalarchives/tdr-terraform-environments) against the same environment. This will revert the change this terraform project has made to the database/url parameter and update the ECS service which forces a restart. Once this is done and the load balancer has switched to the new task, then run: 
```
terraform state rm aws_ssm_parameter.database_url # Stops terraform trying to delete the datbase url parameter.
terraform destroy
```
