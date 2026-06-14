from common.responses import ok, error
from common.dynamo import get_item


def lambda_handler(event, context):
    # TODO: extraer tenantId del authorizer context
    # TODO: extraer {id} de path params
    # TODO: GetItem PK=TENANT#<sede>, SK=ORDER#<id>
    # TODO: retornar pedido o 404
    return error(501, "Not implemented")
