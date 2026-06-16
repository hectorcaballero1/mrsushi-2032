import json
import time
from botocore.exceptions import ClientError
from common.responses import ok, error
from common.dynamo import get_item, get_table
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

    step_data = order.get("steps", {}).get(step, {})

    if not step_data.get("startedAt"):
        # Fase 1: tomar el ticket — escritura condicional para evitar race condition
        table = get_table("ORDERS_TABLE")
        now = int(time.time())
        try:
            table.update_item(
                Key={"PK": order["PK"], "SK": order["SK"]},
                UpdateExpression="SET #steps.#step.#startedAt = :v, #steps.#step.#takenBy = :by",
                ConditionExpression="attribute_not_exists(#steps.#step.#startedAt)",
                ExpressionAttributeNames={
                    "#steps": "steps",
                    "#step": step,
                    "#startedAt": "startedAt",
                    "#takenBy": "takenBy",
                },
                ExpressionAttributeValues={":v": now, ":by": user_id or ""},
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return error(409, "Este ticket ya fue tomado por otro trabajador")
            raise
        return ok({"orderId": order_id, "step": step, "phase": "taken"})

    # Fase 2: marcar listo
    try:
        resume_step(order, step, by=user_id)
    except ValueError as e:
        return error(400, str(e))

    return ok({"orderId": order_id, "step": step, "phase": "completed"})
