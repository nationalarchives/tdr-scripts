# Run a Keycloak instance in the sandbox

**Important Note**: keycloak-sandbox uses v1.5.0 of Terraform. Ensure that Terraform v1.5.0 is installed before proceeding.

This Terraform script lets you create a Keycloak instance in the Sandbox
account. This instance does not have all of the security controls that the
Keycloak instances in the other accounts have. For example, the ECS app runs in
a public subnet rather than a private subnet, the database has a public IP, and
Keycloak only supports HTTP because we do not currently have a subdomain or SSL
certificates for the Sandbox account. This means it is only suitable for testing
out Keycloak configuration changes. It should **never be used to store real
data** or connected to a non-Sandbox service. The Keycloak instance in other
environments should have been created by [tdr-terraform-environments].

This script is intended to be run from a development machine rather than
Jenkins.

For simplicity, the Terraform script uses a local Terraform state rather than
storing the state in a shared S3 bucket. This means only one person can spin up
the Keycloak server at once. If that turns out to be a problem, we can
reconfigure this project to use a shared state.

Remember to tear down the resources once they are not needed.

[tdr-terraform-environments]: https://github.com/nationalarchives/tdr-terraform-environments

## Create and configure the instance

Get AWS credentials for the Sandbox environment by signing in via AWS SSO.

Initialise the project:

```
terraform init
```

Create the AWS resources:

```
terraform apply
```

If you have any conflicts with existing resources, the most likely cause is that
someone else has run this script recently and hasn't run `terraform destroy`
yet.

Upload the Keycloak image to ECR. If you want to use the current intg image,
download it from the mgmt account, replacing the account number in the following
commands:

```
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <mgmt-account-number>.dkr.ecr.eu-west-2.amazonaws.com
docker pull <mgmt-account-number>.dkr.ecr.eu-west-2.amazonaws.com/auth-server:intg
```

Then retag it and upload it to the Sandbox account, replacing the account
numbers in the following commands:

```
docker tag <mgmt-account-number>.dkr.ecr.eu-west-2.amazonaws.com/auth-server:intg <sandbox-account-number>.dkr.ecr.eu-west-2.amazonaws.com/keycloak_sandbox:latest
docker push <sandbox-account-number>.dkr.ecr.eu-west-2.amazonaws.com/keycloak_sandbox:latest
```

Alternatively, if you want to test a modified version of the Docker image, build
it locally then tag and push it as above.

Then restart the ECS service:

```
aws ecs update-service \
  --service keycloak_service_sandbox \
  --cluster keycloak_sandbox \
  --force-new-deployment
```

Check the Keycloak ECS service in the AWS console to check that it has started
up correctly. Once it has, look up the URL of the load balancer:

```
aws elbv2 describe-load-balancers --names "keycloak-sandbox" | grep DNSName
```

Visit this URL in your browser to check that Keycloak is running.

Give yourself temporary access to the database:

```
aws ec2 authorize-security-group-ingress \
  --group-name "keycloak-database-security-group-sandbox" \
  --protocol tcp \
  --port 5432 \
  --cidr <your IP address>/32
```

Look up the address of the Keycloak database instance:

```
aws rds describe-db-instances | grep Address
```

Get the DB account password from systems manager:

```
aws ssm get-parameter --name "/sandbox/keycloak/database/password" --with-decryption
```

Connect to the DB instance, and enter the password when prompted:

```
psql --host=<DB instance address> \
  --port=5432 --user=keycloak_admin --password --dbname keycloak
```

Allow HTTP traffic to Keycloak. This is only safe in the Sandbox environment
where no real data will be stored. Never run this in a non-Sandbox environment!

```
UPDATE realm SET ssl_required='NONE' WHERE id = 'master';
UPDATE realm SET ssl_required='NONE' WHERE id = 'tdr';
```

Then restart the ECS service:

```
aws ecs update-service \
  --service keycloak_service_sandbox \
  --cluster keycloak_sandbox \
  --force-new-deployment
```

Then run `terraform apply` to revert the security group change.

Get the Keycloak admin account details:

```
aws ssm get-parameters \
  --names "/sandbox/keycloak/admin/user" "/sandbox/keycloak/admin/password" \
  --with-decryption
```

Visit the Keycloak load balancer URL again, and sign into the admin UI using the
username and password you just fetched.

## Setup GovUK Notify

**Note**: this step is optional, it is only required if you need to send emails from the sandbox Keycloak instance.

To setup GovUK Notify service update the following AWS SSM secret parameters:
* /sandbox/keycloak/govuk_notify/api_key: this should be a GovUK Notify key that is generated specifically for use in the Sandbox
  * **NOTE**: This Key should be deleted from the GovUK Notify service once no longer needed
* /sandbox/keycloak/govuk_notify/template_id: this should be a GovUK Notify template id

For full documentation on GovUK Notify and how to gain access, see: [TDR Auth Server readme](https://github.com/nationalarchives/tdr-auth-server/blob/master/README.md)

## Delete the instance

Run:

```
terraform destroy
```
