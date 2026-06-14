from common.responses import ok, error
from common.dynamo import get_item


def lambda_handler(event, context):
    auth = event.get("requestContext", {}).get("authorizer", {})
    tenant_id = auth.get("tenantId")

    if not tenant_id:
        return error(403, "tenantId missing from token")

    order_id = event.get("pathParameters", {}).get("id")
    if not order_id:
        return error(400, "Missing order id")

    order = get_item("ORDERS_TABLE", f"TENANT#{tenant_id}", f"ORDER#{order_id}")
    if not order:
        return error(404, "Order not found")

    return ok(order)
