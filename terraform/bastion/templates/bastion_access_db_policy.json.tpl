{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "rds-db:connect",
      "Resource": [
        "arn:aws:rds-db:eu-west-2:${account_id}:dbuser:${instance_id}/bastion_user"
      ]
    }
  ]
}
