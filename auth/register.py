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
    role = body.get("role", "customer")
    tenant_id = body.get("tenantId", "")

    if not email or not password:
        return error(400, "email and password required")

    if role == "worker":
        if not tenant_id:
            return error(400, "tenantId required for workers")
        pk = f"TENANT#{tenant_id}"
    else:
        pk = "BRAND#mrsushi"

    if get_item("USERS_TABLE", pk, f"USER#{email}"):
        return error(409, "User already exists")

    user_id = str(uuid.uuid4())
    pw_hash = hash_password(password)

    item = {
        "PK": pk,
        "SK": f"USER#{email}",
        "GSI1PK": f"USER#{user_id}",
        "userId": user_id,
        "email": email,
        "name": name,
        "role": role,
        "passwordHash": pw_hash,
    }
    if role == "worker":
        item["tenantId"] = tenant_id

    put_item("USERS_TABLE", item)
    return created({"userId": user_id})
