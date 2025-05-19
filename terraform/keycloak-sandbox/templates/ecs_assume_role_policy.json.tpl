{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "${account_id}"
        }
      },
      "Action": [
        "sts:AssumeRole"
      ],
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Sid": ""
    }
  ]
}
