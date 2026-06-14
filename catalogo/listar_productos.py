from common.responses import ok
from common.dynamo import get_table
from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):
    table = get_table("PRODUCTS_TABLE")
    items = table.query(
        KeyConditionExpression=Key("PK").eq("BRAND#mrsushi"),
    ).get("Items", [])
    return ok(items)
