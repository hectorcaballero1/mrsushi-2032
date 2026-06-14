from common.responses import ok, error
from common.dynamo import get_table
from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):
    # TODO: Query PK=BRAND#mrsushi en products table
    # TODO: retornar lista completa (sin paginar)
    return error(501, "Not implemented")
