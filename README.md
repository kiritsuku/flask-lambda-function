# Template for Flask based AWS lambda function

## Motivation

Setting up lambda functions on AWS can be cumbersome since they use their own event based invocation mechanism. The entry point for a Python AWS lambda function could look like this and is called a [lambda function handler](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html):
```python
def lambda_handler(event, context):
    message = f"Hello {event['first_name']} {event['last_name]'}!"
    return {
        'message' : message
    }
```
In case the lambda function is invoked through a HTTP API that is provided through [AWS API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html) the process of handling the requests is unconventional:
```python
import os
import json

def lambda_handler(event, context):
    http = event["requestContext"]["http"]
    path = http["path"]
    method = http["method"]

    if path == "/my/path" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "/my/path exists"
            })
        }
    else:
        return {
            "statusCode": 404
            "body": json.dumps({
                "message": f"Not found: {method} {path}"
            })
        }
```
Since we have to handle the event from API Gateway we can't reuse code from any library or framework that provides a HTTP routing functionality.

Wouldn't it be great if instead we could just use some code written in say [Flask](https://flask.palletsprojects.com/en/2.2.x/quickstart/) directly with API Gateway? Something that would look like this:
```python
from flask import Flask

app = Flask(__name__)

@app.get("/my/path")
def my_path():
    return { "message": "/my/path exists" }
```

In this project it is shown that something very similar can actually be achieved. The Python code

```python
from flask import Blueprint

routes = Blueprint("routes", __name__)

@routes.get("/my/path")
def my_path():
    return { "message": "/my/path exists" }
```

would be able to serve the provided Flask based routes as a lambda function, which only has to include a [lambda layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html) that is able to translate the lambda function event model to a request Flask can understand and repeat the other way around, the translation from a Flask response to a lambda function event response.

## Project Overview

This project consists of three parts:

1. A lambda layer, in `/python-lamdba-layer`. It provides an execution environment for Flask based lambda functions. This lambda layer contains an entry point for Python based lambda functions, which is `main.handler`, in `/python-lamdba-layer/main.py`. The function converts an AWS lambda function event into a [WSGI](https://medium.com/analytics-vidhya/what-is-wsgi-web-server-gateway-interface-ed2d290449e) compatible request, which then can be handled by Flask.

    The layer needs to be built first with `/python-lamdba-layer/build.sh` before it can be deployed.
3. An actual lambda function, in `/api`. It provides a simple AWS HTTP Gateway with three endpoints:
   1. `GET /users`: Retrieve a list of users. Query parameters:
      1. `limit` to configure the number of returned values
      2. `nextToken` to specify the start item
   2. `GET /users/{id}`: Retrieve a user
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

## Similar projects

- [Zappa](https://github.com/zappa/Zappa) - Provides some functionality to make deploying of Python based lambda functions as easy as possible but lacks the ability to create other infrastructure resources (like databases).
- [awsgi](https://github.com/slank/awsgi) - A Python library that can be added to the project but contains some bugs and is unmaintained.
- [serverless-wsgi](https://github.com/logandk/serverless-wsgi) - [Serverless](https://www.serverless.com/) based tool for people who don't want to use Terraform.