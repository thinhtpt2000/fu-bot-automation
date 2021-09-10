import base64


def encode(value):
    return base64.b64encode(value.encode("utf-8"))


def decode(value):
    return base64.b64decode(value).decode("utf-8")
