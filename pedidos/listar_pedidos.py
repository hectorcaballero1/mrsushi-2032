from common.responses import ok, error
from common.dynamo import get_table
from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):
    auth = event.get("requestContext", {}).get("authorizer", {})
    tenant_id = auth.get("tenantId")
    user_id = auth.get("userId")
    role = auth.get("role")

    if not tenant_id:
        return error(403, "tenantId missing from token")

    params = event.get("queryStringParameters") or {}
    status_filter = params.get("status")
    mine = params.get("mine", "false").lower() == "true"

    table = get_table("ORDERS_TABLE")

    if mine and user_id:
        # GSI1: pedidos del customer autenticado
        items = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CUSTOMER#{user_id}"),
            ScanIndexForward=False,
        ).get("Items", [])
    elif status_filter:
        # GSI2: cola FIFO por tenant+status
        items = table.query(
            IndexName="GSI2",
            KeyConditionExpression=Key("GSI2PK").eq(f"TENANT#{tenant_id}#STATUS#{status_filter}"),
            ScanIndexForward=True,
        ).get("Items", [])
    else:
        # Todos los pedidos del tenant (tabla principal)
        items = table.query(
            KeyConditionExpression=Key("PK").eq(f"TENANT#{tenant_id}"),
            ScanIndexForward=False,
        ).get("Items", [])

    return ok(items)
