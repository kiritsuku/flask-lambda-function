from definitions import validate_json
from routes_definitions import CreateUser, PaginatedList, User, scan, dynamodb
import os
from flask import request, Blueprint

table_name = os.environ.get("TABLE_USER_NAME", "teststack-user-v1")

routes = Blueprint("routes", __name__)

@routes.get("/users")
def get_all_user():
    kwargs = {}
    if "nextToken" in request.args:
      kwargs["next_token"] = request.args["nextToken"]
    kwargs["limit"] = request.args.get("limit", 5, type=int)

    items, next_token = scan(table_name, **kwargs)
    users = [User(id=item["userId"], email=item["email"], name=item["name"]) for item in items]
    return PaginatedList.Schema().dump(PaginatedList(
        items=[User.Schema().dump(u) for u in users],
        next_token=next_token,
        number_of_items=len(users)
    ))

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
