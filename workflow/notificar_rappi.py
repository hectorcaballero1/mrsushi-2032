import os
import json
import urllib.request
from common.dynamo import get_item


def lambda_handler(event, context):
    # TODO: extraer detail del evento EventBridge (orderId, tenantId, step)
    # TODO: GetItem orders para obtener externalRef
    # TODO: hacer POST a RAPPI_API_URL/orders/{externalRef}/status con el nuevo estado
    # TODO: manejar errores de conexion con Rappi
    return {"statusCode": 200}
