module "api_lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "4.0.0"

  function_name = "${var.stack_name}-api"
  role_name     = "${local.region}_${var.stack_name}-api"
  handler       = "main.handler"
  runtime       = "python3.9"
  architectures = ["x86_64"]
  memory_size   = 512
  timeout       = 30
  layers        = [module.python_lambda_layer.lambda_layer_arn]

  environment_variables = {
    TABLE_USER_NAME = module.table_user.dynamodb_table_id
  }

  source_path = [
    "../api/routes.py",
    "../api/routes_definitions.py",
  ]

  cloudwatch_logs_retention_in_days = var.cloudwatch_logs_retention_in_days

  publish = true
  allowed_triggers = {
    AllowExecutionFromAPIGateway = {
      service    = "apigateway"
      source_arn = "${module.http_api.apigatewayv2_api_execution_arn}/*/*"
    }
  }
  attach_policy_jsons = true
  policy_jsons = [
    templatefile("./dynamodb-crud-policy.tftpl", {
      table_arns = [
        module.table_user.dynamodb_table_arn,
      ]
    }),
  ]
  number_of_policy_jsons = 1

  tags = local.tags
}

module "http_api" {
  source  = "terraform-aws-modules/apigateway-v2/aws"
  version = "2.2.0"

  name          = "${var.stack_name}-http-api"
  protocol_type = "HTTP"

  # In order to test the CORS configuration on the CLI one has to set the correct headers in the request,
  # otherwhise no `Access-Control-` headers will be present in the response. Example request:
  #
  #   curl -i -XOPTIONS https://<id>.execute-api.<region>.amazonaws.com/<path> -H 'Access-Control-Request-Method: GET' -H 'Origin: http://localhost'
  cors_configuration = {
    allow_methods = ["OPTIONS", "GET", "POST", "PUT", "DELETE"]
    allow_headers = ["*"]
    allow_origins = ["*"]
  }

  create_api_domain_name = false

  integrations = {
    "GET /users" = {
      lambda_arn             = module.api_lambda.lambda_function_arn
      payload_format_version = "2.0"
    }

    "GET /users/{id}" = {
      lambda_arn             = module.api_lambda.lambda_function_arn
      payload_format_version = "2.0"
    }

    "POST /users" = {
      lambda_arn             = module.api_lambda.lambda_function_arn
      payload_format_version = "2.0"
    }
  }

  tags = local.tags
}

