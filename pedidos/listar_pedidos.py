from common.responses import ok, error
from common.dynamo import query, get_table
from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):
    # TODO: leer query params (status, mine)
    # TODO: si mine => GSI1 (CUSTOMER#<userId>)
    # TODO: si status => GSI2 (TENANT#<sede>#STATUS#<status>)
    # TODO: si no hay filtros => listar todos los de la sede
    return error(501, "Not implemented")
