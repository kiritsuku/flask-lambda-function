# Template for Flask based AWS lambda function

This project consists of three parts:

1. A lambda layer, in `/python-lamdba-layer`. It provides an execution environment for Flask based lambda functions. This lambda layer contains an entry point for Python based lambda functions, which is `main.handler`, in `/python-lamdba-layer/main.py`. The function converts an AWS lambda function event into a [WSGI](https://medium.com/analytics-vidhya/what-is-wsgi-web-server-gateway-interface-ed2d290449e) compatible request, which then can be handled by Flask.

    The layer needs to be built first with `/python-lamdba-layer/build.sh` before it can be deployed.
3. An actual lambda function, in `/api`. It provides a simple AWS HTTP Gateway with three endpoints:
   1. `GET /users`: Retrieve a user
   2. `GET /users/{id}`: Retrieve all users
   3. `POST /users`: Create a user. Payload: `{ "name": "string", "email": "string" }`

   The user data is stored in and retrieved from a DynamoDB table.
4. The AWS infrastructure provisioned through Terraform, in `/infra`. Build and deploy with `terraform init && terraform apply`. The AWS profile `demo-user` needs to be configured in `~/.aws/credentials`.

    To create a lambda function that is based on the provided lambda layer, the following Terraform code can be used:
    ```tf
    module "lambda" {
        source  = "terraform-aws-modules/lambda/aws"
        version = "4.0.0"

        function_name = "a-name-for-the-lambda"
        handler       = "main.handler" # (1)
        runtime       = "python3.9"
        architectures = ["x86_64"]
        memory_size   = 512
        timeout       = 30
        layers        = [module.python_lambda_layer.lambda_layer_arn]

        source_path = [
            "routes.py", # (2)
        ]

        publish = true
        allowed_triggers = {
            AllowExecutionFromAPIGateway = {
                service    = "apigateway"
                source_arn = "${module.http_api.apigatewayv2_api_execution_arn}/*/*"
            }
        }
    }
    ```
    The values `(1)` and `(2)` can't be changed, since these values are hardcoded in the lambda layer. The Python based lambda function would look like this:
    ```python
    # filename: routes.py (2)
    from flask import Blueprint

    routes = Blueprint("routes", __name__) # (3)

    @routes.get("/endpoint")
    def endpoint():
        return { "value": "Hello World" }
    ```
    Again, the value `routes` at `(3)` needs to be called this way, in the same way how the file name at `(2)` is also required to be named this way.