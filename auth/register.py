import json
import uuid
import hashlib
from common.responses import created, error
from common.dynamo import put_item, get_item


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    name = body.get("name", "")

    if not email or not password:
        return error(400, "email and password required")

    if get_item("USERS_TABLE", "BRAND#mrsushi", f"USER#{email}"):
        return error(409, "User already exists")

    user_id = str(uuid.uuid4())

    put_item("USERS_TABLE", {
        "PK": "BRAND#mrsushi",
        "SK": f"USER#{email}",
        "GSI1PK": f"USER#{user_id}",
        "userId": user_id,
        "email": email,
        "name": name,
        "role": "customer",
        "passwordHash": hash_password(password),
    })
    return created({"userId": user_id})
