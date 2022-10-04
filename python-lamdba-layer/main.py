import logging
import aws_lambda_wsgi_adapter
from flask import Flask
"""
The `routes` definition needs to be defined in the lambda function that imports this Flask based lambda layer.
It can be defined like this:

  # in a file called `routes.py`
  from flask import Blueprint
  routes = Blueprint('routes', __name__)
"""
from routes import routes

# Set the logger for both the lambda environment and a local environment correctly
# See: https://stackoverflow.com/questions/37703609/using-python-logging-with-aws-lambda
if logging.getLogger().hasHandlers():
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO, format = "[%(levelname)s] %(name)s - %(message)s")

headers = {
    "Content-Type": "application/json",
    "X-Custom-Header": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE",
    "Access-Control-Allow-Headers": "Accept, Content-Type, Origin",
}

app = Flask(__name__)
app.register_blueprint(routes)

@app.after_request
def after_request(response):
    response.headers = headers
    return response

@app.errorhandler(Exception)
def handle_error(err):
    logging.exception(err)
    return { "message": f"An error occured on the server: {err}" }, 500

# Event type: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format
# Context type: https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
def handler(event, context):
    return aws_lambda_wsgi_adapter.response(app, event, context)
