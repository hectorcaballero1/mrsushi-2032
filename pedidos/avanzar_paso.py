import json
from common.responses import ok, error
from common.dynamo import get_item
from common.workflow_helper import resume_step
from common.authz import STEP_TO_ALLOWED_ROLES, require_role


def lambda_handler(event, context):
    claims = event.get("requestContext", {}).get("authorizer", {})
    tenant_id = claims.get("tenantId")
    user_id = claims.get("userId")

    if not tenant_id:
        return error(403, "tenantId missing from token")

    order_id = event.get("pathParameters", {}).get("id")
    if not order_id:
        return error(400, "Missing order id")

    body = json.loads(event.get("body") or "{}")
    step = body.get("step")
    if not step:
        return error(400, "Missing step")

    allowed = STEP_TO_ALLOWED_ROLES.get(step, [])
    if not require_role(claims, allowed):
        return error(403, "rol no autorizado para este paso")

    order = get_item("ORDERS_TABLE", f"TENANT#{tenant_id}", f"ORDER#{order_id}")
    if not order:
        return error(404, "Order not found")

    try:
        resume_step(order, step, by=user_id)
    except ValueError as e:
        return error(400, str(e))

    return ok({"orderId": order_id, "step": step})
