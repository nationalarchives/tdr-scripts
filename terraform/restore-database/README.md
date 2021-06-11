# Restore a database

`terraform init`
`terraform import aws_ssm_parameter.database_url /intg/consignmentapi/database/url`
`terraform apply -var tdr_account_number=xxxxxxxx`
