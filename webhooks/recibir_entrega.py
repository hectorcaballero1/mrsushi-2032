import os
import json
import time
from common.responses import ok, error
from common.dynamo import get_item, update_item


def lambda_handler(event, context):
    headers = event.get("headers", {})
    api_key = headers.get("x-api-key") or headers.get("X-Api-Key")

    if api_key != os.environ.get("RAPPI_WEBHOOK_SECRET"):
        return error(401, "Unauthorized")

    body = json.loads(event.get("body", "{}"))
    tenant_id = body.get("tenantId")
    order_id = body.get("orderId")
    if not tenant_id or not order_id:
        return error(400, "Missing tenantId or orderId")

    order = get_item("ORDERS_TABLE", f"TENANT#{tenant_id}", f"ORDER#{order_id}")
    if not order:
        return error(404, "Order not found")

    update_item(
        "ORDERS_TABLE",
        f"TENANT#{tenant_id}",
        f"ORDER#{order_id}",
        {"status": "entregado", "deliveredAt": body.get("deliveredAt", int(time.time()))},
    )

    return ok({"message": "Order delivered"})
