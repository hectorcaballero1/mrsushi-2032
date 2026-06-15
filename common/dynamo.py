import os
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")


def get_table(name):
    return dynamodb.Table(os.environ[name])


def get_item(table_name, pk, sk):
    table = get_table(table_name)
    return table.get_item(Key={"PK": pk, "SK": sk}).get("Item")


def put_item(table_name, item, condition=None):
    table = get_table(table_name)
    kwargs = {"Item": item}
    if condition:
        kwargs["ConditionExpression"] = condition
    table.put_item(**kwargs)


def update_item(table_name, pk, sk, updates):
    table = get_table(table_name)
    expr = "SET " + ", ".join(f"#{k}=:v{i}" for i, k in enumerate(updates))
    names = {f"#{k}": k for k in updates}
    vals = {f":v{i}": v for i, v in enumerate(updates.values())}
    table.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=vals,
    )


def query_items(table_name, pk, sk_prefix=None):
    table = get_table(table_name)
    condition = Key("PK").eq(pk)
    if sk_prefix:
        condition &= Key("SK").begins_with(sk_prefix)
    return table.query(KeyConditionExpression=condition).get("Items", [])


def query(table_name, index_name, key_condition, asc=True):
    table = get_table(table_name)
    return table.query(
        IndexName=index_name,
        KeyConditionExpression=key_condition,
        ScanIndexForward=asc,
    ).get("Items", [])
