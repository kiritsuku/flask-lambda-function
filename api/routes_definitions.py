from typing import ClassVar, Type
from marshmallow import Schema
from marshmallow_dataclass import dataclass

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
