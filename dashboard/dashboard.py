from common.responses import ok, error
from common.dynamo import get_table
from boto3.dynamodb.conditions import Key

STATUSES = ["recibido", "cocinando", "empacando", "repartiendo", "entregando_a_rappi", "entregado"]


def lambda_handler(event, context):
    auth = event.get("requestContext", {}).get("authorizer", {})
    role = auth.get("role")
    tenant_id = auth.get("tenantId")

    if role != "admin":
        return error(403, "Admin only")
    if not tenant_id:
        return error(403, "tenantId missing from token")

    table = get_table("ORDERS_TABLE")

    por_status = {}
    for status in STATUSES:
        items = table.query(
            IndexName="GSI2",
            KeyConditionExpression=Key("GSI2PK").eq(f"TENANT#{tenant_id}#STATUS#{status}"),
            Select="COUNT",
        ).get("Count", 0)
        por_status[status] = items

    return ok({"porStatus": por_status, "tenantId": tenant_id})
