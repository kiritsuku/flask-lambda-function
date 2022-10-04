"""
This is a WSGI adapter for AWS lambda. At allows to use WSGI-compatible middleware like Flask with AWS lambda.

Code adapted from https://github.com/slank/awsgi and https://github.com/logandk/serverless-wsgi
"""
from base64 import b64encode, b64decode
from io import BytesIO
import itertools
import collections
import sys
from urllib.parse import urlencode
from werkzeug.datastructures import Headers

# Convert bytes to str, if required
def convert_str(s):
    return s.decode("utf-8") if isinstance(s, bytes) else s

# Convert str to bytes, if required
def convert_byte(b):
    return b.encode("utf-8", errors="strict") if isinstance(b, str) else b

def convert_b46(s):
    return b64encode(s).decode("ascii")

class StartResponse(object):
    def __init__(self, base64_content_types=None):
        """
        Args:
            base64_content_types (set): Set of HTTP Content-Types which should
            return a base64 encoded body. Enables returning binary content from
            API Gateway.
        """
        self.status = 500
        self.status_line = "500 Internal Server Error"
        self.headers = []
        self.chunks = collections.deque()
        self.base64_content_types = set(base64_content_types or []) or set()

    def __call__(self, status, headers, exc_info=None):
        self.status_line = status
        self.status = int(status.split()[0])
        self.headers[:] = headers
        return self.chunks.append

    def use_binary_response(self, headers, body):
        content_type = headers.get("Content-Type")

        if content_type and ";" in content_type:
            content_type = content_type.split(";")[0]
        return content_type in self.base64_content_types

    def build_body(self, headers, output):
        totalbody = b"".join(itertools.chain(
            self.chunks, output,
        ))

        is_b64 = self.use_binary_response(headers, totalbody)

        if is_b64:
            converted_output = convert_b46(totalbody)
        else:
            converted_output = convert_str(totalbody)

        return {
            "isBase64Encoded": is_b64,
            "body": converted_output,
        }

    def response(self, output):
        headers = dict(self.headers)

        rv = {
            "statusCode": self.status,
            "headers": headers,
        }
        rv.update(self.build_body(headers, output))
        return rv


class StartResponseGateway(StartResponse):
    def response(self, output):
        rv = super(StartResponseGateway, self).response(output)

        rv["statusCode"] = str(rv["statusCode"])

        return rv

def environ(event, context):
    body = event.get("body", "")

    if event.get("isBase64Encoded", False):
        body = b64decode(body)
    # FIXME: Flag the encoding in the headers
    body = convert_byte(body)
    headers = Headers(event["headers"])

    environ = {
        "CONTENT_LENGTH": str(len(body)),
        "CONTENT_TYPE": headers.get("Content-Type", ""),
        "PATH_INFO": event["path"] if "path" in event else event["requestContext"]["http"]["path"],
        "QUERY_STRING": urlencode(event.get("queryStringParameters", {})),
        "REMOTE_ADDR": event.get("identity", event.get("sourceIp", "")),
        "REMOTE_USER": event.get("principalId", ""),
        "REQUEST_METHOD": event["httpMethod"] if "httpMethod" in event else event["requestContext"]["http"]["method"],
        "SCRIPT_NAME": "",
        "SERVER_NAME": headers.get("Host", "lambda"),
        "SERVER_PORT": headers.get("X-Forwarded-Port", "80"),
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.errors": sys.stderr,
        "wsgi.input": BytesIO(body),
        "wsgi.multiprocess": False,
        "wsgi.multithread": False,
        "wsgi.run_once": False,
        "wsgi.url_scheme": headers.get("X-Forwarded-Proto", "http"),
        "wsgi.version": (1, 0),
        "lambda.event": event,
        "lambda.context": context,
    }

    # Keep the lambda authorizer value easily accessible if it exists
    try:
        environ["lambda.authorizer"] = event["requestContext"]["authorizer"]["lambda"]
    except KeyError:
        pass

    for k, v in headers.items():
        k = "HTTP_" + k.upper().replace("-", "_")
        if k not in ("HTTP_CONTENT_TYPE", "HTTP_CONTENT_LENGTH"):
            environ[k] = v

    return environ

def response(app, event, context, base64_content_types=None):
    sr = StartResponseGateway(base64_content_types=base64_content_types)
    output = app(environ(event, context), sr)
    return sr.response(output)
