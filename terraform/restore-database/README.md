# Restore a database

This script creates a replica of an existing rds database from a snapshot. It also updates the database url parameter in the parameter store to point to the new database instance.

This script is intended to be used to recover lost data in an emergency if it has been accidentally deleted, or major problem has affected the main database.

Any changes that affect the production database should be made by two people, either sitting together or screen sharing. This is to help prevent mistakes and for accountability.

## Outline of steps for restoring database from snapshot
1. Identify which snapshot to restore from either the latest, or a point in time version
2. Run the Terraform. This will
    * Create a new database instance from the chosen snapshot version;
    * Update the database url SSM parameter to point to the new instance endpoint
    * Update the ECS task role to have permission to access the database using the database user
3. Restart the ECS service to pick up the restored instance of the DB
4. Check that the ECS service starts up and is running correctly with the restored instance of the DB
   * If restoring the Keycloak DB instance depending on the snapshot version the client secrets stored in the SSM parameter store maybe out of snyc with the secrets held in the restore DB. If so the SSM parameter values will need to be updated to the values held in Keycloak
5. Update the Terraform environments state to match with the restored DB instance
6. Destroy the old version of the database
   * **Note**: only do this once satisfied everything is working and the restore DB instance is stable

## Run terraform

**Important Note**: restore-database uses v1.9.8 of Terraform. Ensure that Terraform v1.9.8 is installed before proceeding.

1. Set the relevant environment variables:
   * `export TF_VAR_database=consignment-api` or `export TF_VAR_database=keycloak`
   * `export DB_NO_DASH=$(echo $TF_VAR_database | sed  's/-//g')` (helper variable as some fields need `consignmentapi` and some need `consignment-api)
   * `export TF_VAR_tdr_account_number=xxxxxxxxxxx`
   * `export TF_VAR_instance_identifier=$(aws rds describe-db-instances --query="DBInstances[?DBName=='$DB_NO_DASH'].DBInstanceIdentifier" --output text)`
   * `export TF_VAR_engine_version=$(aws rds describe-db-instances --query="DBInstances[?DBName=='$DB_NO_DASH'].EngineVersion" --output text)`
   * `export TF_VAR_restore_time=YYYY-MM-DDThh:mm:ssZ` (optional if need to restore DB to a point in time instead of latest possible version. UTC format see further details here: [restore_time](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance#restore_time))
   * `export TF_VAR_availability_zone=eu-west-2a` (this should match the availability zone of the instance being restored)
   * `export PROFILE=intg` (replace with staging or prod if using those environments)
2. Run the Terraform
   * Terraform `plan` should be run first to ensure the restore DB has the correct setting / naming
   ```
   terraform init
   terraform workspace new intg # replace with staging or prod if using those environments
   terraform apply
   ```

The restore may take 10-15 minutes depending on the size of the database when you run this. Terraform won't exit until the instance is created.

## Restart the ECS service to pick up the new database

```
aws ecs update-service --service $DB_NO_DASH_service_$PROFILE --cluster $DB_NO_DASH_$PROFILE --force-new-deployment
```

## Revert Keycloak Secrets If Required

If restoring the Keycloak database depending on the age of the snapshot used to restore, the client secret keys may be out of sync.

To resolve this copy the current client secret keys from Keycloak to the relevant AWS SSM parameter

## Update the Terraform state to match restored DB instance

Update the Terraform environments state to match with the restored DB instance
1. Remove old DB instance from Terraform state: `terraform rm module.{database module name}.aws_db_instance.db_instance`
2. Import the restored DB instance into the Terraform state: `terraform import module.{database module name}.aws_db_instance.db_instance {DB instance id}`
3. Remove old random identifier from Terraform state: `terraform rm module.{database module name}.random_string.identifier_string`
4. Import the new random identifier into the Terraform state: `terraform import module.{database module name}.aws_db_instance.db_instance {random identifier id}`
5. Run Terraform apply. This will cause the DB instance to rename which will mean the Terraform apply will eventually error
6. Run Terraform apply again and the Terraform should fully apply as it will pick up the newly renamed restore DB instance
7. Run Terraform apply again to ensure the state is stable, ie there are no longer changes appearing for the restore DB instance
