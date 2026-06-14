import os
import jwt
import time

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me")
ALGORITHM = "HS256"


def emit_token(payload):
    payload["iat"] = int(time.time())
    payload["exp"] = int(time.time()) + 86400  # 24h
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def validate_token(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
