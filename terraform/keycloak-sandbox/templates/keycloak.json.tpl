[
  {
    "name": "keycloak",
    "image": "${app_image}",
    "cpu": 0,
    "secrets": [
      {
        "valueFrom": "${url_path}",
        "name": "KC_DB_URL_HOST"
      },
      {
        "valueFrom": "${username_path}",
        "name": "KC_DB_USERNAME"
      },
      {
        "valueFrom": "${password_path}",
        "name": "KC_DB_PASSWORD"
      },
      {
        "valueFrom": "${admin_user_path}",
        "name": "KEYCLOAK_ADMIN"
      },
      {
        "valueFrom": "${admin_password_path}",
        "name": "KEYCLOAK_ADMIN_PASSWORD"
      },
      {
        "valueFrom" : "${client_secret_path}",
        "name": "CLIENT_SECRET"
      },
      {
        "valueFrom": "${backend_checks_client_secret_path}",
        "name": "BACKEND_CHECKS_CLIENT_SECRET"
      },
      {
        "valueFrom": "${realm_admin_client_secret_path}",
        "name": "REALM_ADMIN_CLIENT_SECRET"
      },
      {
        "valueFrom": "${configuration_properties_path}",
        "name": "KEYCLOAK_CONFIGURATION_PROPERTIES"
      },
      {
        "valueFrom": "${user_admin_client_secret_path}",
        "name": "USER_ADMIN_CLIENT_SECRET"
      },
      {
        "valueFrom": "${govuk_notify_api_key_path}",
        "name": "GOVUK_NOTIFY_API_KEY"
      },
      {
        "valueFrom": "${govuk_notify_template_id_path}",
        "name": "GOVUK_NOTIFY_TEMPLATE_ID"
      },
      {
        "valueFrom": "${reporting_client_secret_path}",
        "name": "REPORTING_CLIENT_SECRET"
      }
    ],
    "environment": [
      {
        "name": "KEYCLOAK_HOST",
        "value": "auth.tdr-sandbox.nationalarchives.gov.uk"
      },
      {
        "name" : "FRONTEND_URL",
        "value" : "${frontend_url}"
      },
      {
        "name" : "KC_DB",
        "value" : "postgres"
      },
      {
        "name" : "KEYCLOAK_IMPORT",
        "value": "/tmp/tdr-realm.json"
      },
      {
        "name": "SNS_TOPIC_ARN",
        "value": "${sns_topic_arn}"
      },
      {
        "name": "TDR_ENV",
        "value": "${app_environment}"
      }
    ],
    "networkMode": "awsvpc",
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/keycloak-${app_environment}",
        "awslogs-region": "${aws_region}",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "portMappings": [
      {
        "containerPort": 8080,
        "hostPort": 8080
      }
    ]
  }
]
