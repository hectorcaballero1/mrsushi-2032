import json
from common.responses import ok, error
from common.dynamo import get_item
from common.jwt_helper import emit_token
from auth.register import hash_password


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
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

    user = get_item("USERS_TABLE", pk, f"USER#{email}")
    if not user:
        return error(401, "Invalid credentials")

    if user.get("passwordHash") != hash_password(password):
        return error(401, "Invalid credentials")

    payload = {"sub": user["userId"], "role": user.get("role", role)}
    if role == "worker":
        payload["tenantId"] = tenant_id

    token = emit_token(payload)
    return ok({"token": token, "userId": user["userId"], "role": user.get("role", role)})
