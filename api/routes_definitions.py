from typing import ClassVar, Type, Dict, List, Tuple, Any
from marshmallow import Schema
from marshmallow_dataclass import dataclass
import os, base64, json
# In order to get type annotations for boto3, one has to install this: https://pypi.org/project/boto3-stubs/
import boto3

@dataclass
class User:
    id: str
    email: str
    name: str
    Schema: ClassVar[Type[Schema]] = Schema

@dataclass
class CreateUser:
    email: str
    name: str
    Schema: ClassVar[Type[Schema]] = Schema

@dataclass
class PaginatedList:
    items: List[Dict[str, Any]]
    nextToken: str
    numberOfItems: int
    Schema: ClassVar[Type[Schema]] = Schema

# If we run the code locally we have to set a profile explicitly using the env_var AWS_PROFILE
if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    session = boto3.Session(profile_name=os.environ.get("AWS_PROFILE", "demo-user"))
    dynamodb = session.resource("dynamodb")
else:
    dynamodb = boto3.resource("dynamodb")

def scan(table_name: str, limit: int = 10, next_token: str = None) -> Tuple[List[Dict[str, object]], str]:
    """
    Returns:
        A tuple of `items` and `next_token`. If there are no more elements `next_token` is `None`.

    Example usage:
    ```
        # in case no next token exists
        items, next_token = scan("table_name")

        # in case a next token already exists
        items, next_token = scan("table_name", next_token=token)
    ```
    """
    def encode_key(key: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(key).encode("utf-8")).decode("utf-8")

    def decode_key(key: str) -> dict:
        return json.loads(base64.urlsafe_b64decode(key))

    if next_token != None:
        resp = dynamodb.Table(table_name).scan(
            Limit=limit,
            ExclusiveStartKey=decode_key(next_token))
    else:
        resp = dynamodb.Table(table_name).scan(Limit=limit)

    if "LastEvaluatedKey" in resp:
        return (resp["Items"], encode_key(resp["LastEvaluatedKey"]))
    else:
        return (resp["Items"], None)

def all_items(table_name: str) -> List[Dict[str, object]]:
    """
    Returns:
        All items of table `table_name`.
    """
    limit = 500
    items, next_token = scan(table_name, limit)
    while next_token != None:
        new_items, next_token = scan(table_name, limit, next_token=next_token)
        items.extend(new_items)
    return items
