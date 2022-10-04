from typing import Any, Callable, ClassVar, Dict, List, Literal, Optional, Type
from marshmallow import EXCLUDE, Schema, post_dump
from marshmallow_dataclass import dataclass
from marshmallow.exceptions import ValidationError

# Marshmallow docs:
# - https://pypi.org/project/marshmallow-dataclass/
@dataclass
class HttpContext:
    method: str
    path: str
    protocol: str
    sourceIp: str
    userAgent: str
    Schema: ClassVar[Type[Schema]] = Schema

@dataclass
class RequestContext:
    accountId: str
    apiId: str
    domainName: str
    domainPrefix: str
    requestId: str
    routeKey: str
    stage: str
    time: str
    timeEpoch: int
    http: HttpContext
    authorizer: Optional[dict]
    Schema: ClassVar[Type[Schema]] = Schema

@dataclass
class HttpEvent():
    version: Literal["2.0"]
    routeKey: str
    rawPath: str
    rawQueryString: str
    headers: Dict[str, str]
    requestContext: RequestContext
    body: Optional[str]
    isBase64Encoded: bool
    Schema: ClassVar[Type[Schema]] = Schema

    # https://marshmallow.readthedocs.io/en/latest/quickstart.html#unknown
    class Meta:
        unknown = EXCLUDE

@dataclass
class HttpResponseEvent:
    statusCode: int = None
    body: str = None
    headers: Dict[str, str] = None
    multiValueHeaders: Dict[str, List[str]] = None
    isBase64Encoded: bool = False
    Schema: ClassVar[Type[Schema]] = Schema

# How to skip default values like None
# https://stackoverflow.com/questions/55108696/json-serialization-using-marshmallow-skip-none-attributes
class BaseSchema:
    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return { k: v for k, v in data.items() if v is not None }

def validate_json(schema: Type[Schema], payload: bytes, f: Callable[[Any], Any]):
    try:
        obj = schema().loads(payload.decode("utf-8"))
        return f(obj)
    except ValidationError as e:
        return str(e), 400
