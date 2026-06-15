import json
import uuid
from common.responses import created, ok, error
from common.dynamo import put_item, query_items
from common.authz import require_role
from auth.register import hash_password
from botocore.exceptions import ClientError

VALID_ROLES = {"cocinero", "despachador", "delivery"}


def crear_staff(event, context):
    claims = event["requestContext"]["authorizer"]
    if not require_role(claims, ["admin"]):
        return error(403, "Forbidden")

    body = json.loads(event.get("body") or "{}")
    name = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    role = body.get("role", "")

    if not name or not email or not password:
        return error(400, "name, email and password required")
    if role not in VALID_ROLES:
        return error(400, f"role must be one of: {', '.join(sorted(VALID_ROLES))}")

    tenant_id = claims["tenantId"]
    user_id = str(uuid.uuid4())

    try:
        put_item("USERS_TABLE", {
            "PK": f"TENANT#{tenant_id}",
            "SK": f"USER#{email}",
            "GSI1PK": f"USER#{user_id}",
            "userId": user_id,
            "email": email,
            "name": name,
            "role": role,
            "tenantId": tenant_id,
            "passwordHash": hash_password(password),
        }, condition="attribute_not_exists(PK)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return error(409, "User already exists")
        raise

    return created({"userId": user_id})


def listar_staff(event, context):
    claims = event["requestContext"]["authorizer"]
    if not require_role(claims, ["admin"]):
        return error(403, "Forbidden")

    tenant_id = claims["tenantId"]
    items = query_items(
        "USERS_TABLE",
        pk=f"TENANT#{tenant_id}",
        sk_prefix="USER#",
    )

    staff = [
        {k: v for k, v in u.items() if k != "passwordHash"}
        for u in items
    ]
    return ok(staff)
