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

### Restoring from AWS Backup Vault

In the event of a full environment the RDS databases will need to be restored from the AWS backup vault.

The steps to do this are outlined in the documentation [Cross Account Recovery RDS](https://github.com/nationalarchives/ds-infrastructure-aws-backup/blob/main/docs/cross-account-recovery-rds.md)

The steps cover points 1 and 2 above. The other steps 3 to 6 above still need to be undertaken once the RDS database is restored from the AWS backup vault. 

## Run terraform

**Important Note**: restore-database uses v1.9.8 of Terraform. Ensure that Terraform v1.9.8 is installed before proceeding. Also ensure you have valid aws credentials. You should use intg,staging or prod account credentials.

**Note**: this step is not necessary when restoring from the AWS backup vault.

1. Set the relevant environment variables:
   * Update your AWS credentials with credentials for the TDR environment you are restoring the DB in.
   * `export TF_VAR_database=consignmentapi` or `export TF_VAR_database=keycloak`
   * `export DB_NO_DASH=$(echo $TF_VAR_database | sed  's/-//g')` (helper variable as some fields need `consignmentapi` and some need `consignment-api)
   * `export TF_VAR_tdr_account_number=xxxxxxxxxxx`
   * `export TF_VAR_instance_identifier=$(aws rds describe-db-instances --query="DBInstances[?DBName=='$DB_NO_DASH'].DBInstanceIdentifier" --output text)`
   * `export TF_VAR_engine_version=$(aws rds describe-db-instances --query="DBInstances[?DBName=='$DB_NO_DASH'].EngineVersion" --output text)`
   * `export TF_VAR_restore_time=YYYY-MM-DDThh:mm:ssZ` (optional if need to restore DB to a point in time instead of latest possible version. UTC format see further details here: [restore_time](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance#restore_time))
   * `export TF_VAR_instance_availability_zone=eu-west-2a` (this should match the availability zone of the instance being restored)
   * `export PROFILE=intg` (replace with staging or prod if using those environments)
2. Run the Terraform
   * Update your AWS credentials with TDR Management account credentials
   * Terraform `plan` should be run first to ensure the restore DB has the correct setting / naming
   ```
   terraform init
   terraform workspace new intg # replace with staging or prod if using those environments
   terraform apply
   ```

The restore may take 10-15 minutes depending on the size of the database when you run this. Terraform won't exit until the instance is created.

## Update Policies to point to new database 

The `consignmentapi_ecs_task_role_{env}` or `KeycloakECSTaskRole{env}` role will have a new policy attached called `RestoredDbAccessPolicy{env}`.
* copy the resource ARN of the `RestoredDbAccessPolicyIntg` and overwrite the resource ARN of the `TDRConsignmentApiAllowIAMAuthPolicy{env}` or `KeycloakECSTaskPolicy{env}`

## Update SSM parameters to point to new database
There will be a new entry in SSM parameter store called `/{env}/consignmentapi/database/url`
* Copy the value from `/{env}/{database}/database/url` and overwrite the ssm parameter for `/intg/{database}/instance/url` with that value

## Restart the ECS service to pick up the new database

```
aws ecs update-service --service $DB_NO_DASH_service_$PROFILE --cluster $DB_NO_DASH_$PROFILE --force-new-deployment
```

Alternatively you can do this manually via the AWS console by navigating to Amazon Elastic Container Service > Clusters > {ECS_Service}_
{env} > Services and then clicking update > force new deployment. 

## Revert Keycloak Secrets If Required

If restoring the Keycloak database depending on the age of the snapshot used to restore, the client secret keys may be out of sync.

To resolve this copy the current client secret keys from Keycloak to the relevant AWS SSM parameter

## Update the Terraform state to match restored DB instance

**Note**: Before making Terraform state changes take a backup copy of the existing TDR environment state from the AWS S3 state bucket.

Update the Terraform environments state to match with the restored DB instance.

In your local `tdr-terraform-environments` repo:
1. Update your AWS credentials with TDR Management account credentials
2. Remove old DB instance from Terraform state: `terraform state rm module.{database module name}.aws_db_instance.db_instance`
3. Import the restored DB instance into the Terraform state: `terraform import module.{database module name}.aws_db_instance.db_instance { restored DB instance id}`
4. Remove old random identifier from Terraform state: `terraform state rm module.{database module name}.random_string.identifier_string`
5. Import the new random identifier into the Terraform state: `terraform import module.{database module name}.random_string.identifier_string { restored random identifier id - this can be found in the local Terraform state file created when applying the restore Terraform }`
6. Run Terraform apply. This will cause the DB instance to rename.
7. Run Terraform apply again and the Terraform should fully apply as it will pick up the newly renamed restored DB instance
8. Run Terraform apply again to ensure the state is stable, ie there are no longer changes appearing for the restored DB instance
9. Restart the ECS task  again so it picks up the new stable DB instance.

## Cleanup SSM Parameter store and policies
Once the system is up and running with the new database snapshot, the temporarily created ssm parameter and policies will need to be deleted.
* Delete the `RestoredDbAccessPolicyIntg` policy
* Delete the `/{env}/{database}/database/url` ssm parameter
* If relevant delete the old version of the DB
