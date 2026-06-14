import os
import json
from common.responses import ok, error
from common.workflow_helper import get_order_by_external_ref, resume_step


def lambda_handler(event, context):
    headers = event.get("headers", {})
    api_key = headers.get("x-api-key") or headers.get("X-Api-Key")

    if api_key != os.environ.get("RAPPI_WEBHOOK_SECRET"):
        return error(401, "Unauthorized")

    body = json.loads(event.get("body", "{}"))
    # Rappi manda su propio id en "orderId" — lo buscamos por GSI3 (externalRef)
    external_ref = body.get("orderId")
    if not external_ref:
        return error(400, "Missing orderId")

    order = get_order_by_external_ref(external_ref)
    if not order:
        return error(404, "Order not found")

    try:
        resume_step(order, "entregar_rappi")
    except ValueError as e:
        return error(400, str(e))

    return ok({"message": "Delivery confirmed"})
