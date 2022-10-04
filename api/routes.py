from definitions import validate_json
from routes_definitions import CreateUser, User
import os, logging, json
# In order to get type annotations for boto3, one has to install this: https://pypi.org/project/boto3-stubs/
import boto3
from flask import request, Blueprint

# If we run the code locally we have to set a profile explicitly using the env_var AWS_PROFILE
if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE", "demo-user"))
    dynamodb = session.resource("dynamodb")
else:
    dynamodb = boto3.resource("dynamodb")

table_name = os.environ.get("TABLE_USER_NAME", "teststack-user-v1")

routes = Blueprint("routes", __name__)

@routes.get("/users")
def get_all_user():
    limit = 50
    resp = dynamodb.Table(table_name).scan(Limit=limit)
    items = resp["Items"]
    users = [User(id=item["userId"], email=item["email"], name=item["name"]) for item in items]
    return [User.Schema().dumps(u) for u in users]

@routes.get("/users/<id>")
def get_user(id: str):
    resp = dynamodb.Table(table_name).get_item(
        Key={"userId": id}
    )
    item = resp["Item"]
    u = User(id=item["userId"], email=item["email"], name=item["name"])
    return User.Schema().dumps(u)

@routes.post("/users")
def create_user():
    def handle_create_user(user: CreateUser):
        u = User(
            id=unique_id(),
            email=user.email,
            name=user.name,
        )
        dynamodb.Table(table_name).put_item(
            Item={
                "userId": u.id,
                "email": u.email,
                "name": u.name,
            },
        )
        return User.Schema().dumps(u)
    return validate_json(CreateUser.Schema, request.data, handle_create_user)

def unique_id(entropy: int = 20) -> str:
    """
    See https://neilmadden.blog/2018/08/30/moving-away-from-uuids/ for an explanation about the implementation.
    """
    import secrets
    return secrets.token_urlsafe(entropy)
