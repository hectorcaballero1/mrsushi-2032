from common.responses import ok, error
from common.dynamo import get_table
from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):
    auth = event.get("requestContext", {}).get("authorizer", {})
    tenant_id = auth.get("tenantId")
    user_id = auth.get("userId")

    params = event.get("queryStringParameters") or {}
    status_filter = params.get("status")
    mine = params.get("mine", "false").lower() == "true"

    table = get_table("ORDERS_TABLE")

    # Historial del cliente: consulta por CLIENTE (GSI1), no por sede.
    # Un cliente puede pedir de varias sedes, así que este camino NO usa tenantId.
    # Pedidos de invitado/Rappi no tienen GSI1PK (sparse) → no aparecen aquí.
    if mine:
        if not user_id:
            return error(401, "token sin userId")
        items = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("GSI1PK").eq(f"CUSTOMER#{user_id}"),
            ScanIndexForward=False,
        ).get("Items", [])
        return ok(items)

    # Cola de trabajo (worker): sí requiere tenantId del token.
    if not tenant_id:
        return error(403, "tenantId missing from token")

    if status_filter:
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
