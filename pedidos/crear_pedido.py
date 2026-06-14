import uuid
import json
from datetime import datetime
from common.responses import created, error
from common.dynamo import put_item
from common.events import put_event


def lambda_handler(event, context):
    # TODO: parsear body (items, customer, source, tenantId)
    # TODO: calcular tieneFria / tieneCaliente segun items
    # TODO: generar orderId (uuid)
    # TODO: armar item de pedido con PK=TENANT#<sede>, SK=ORDER#<id>
    # TODO: guardar en orders table con status=pendiente, steps vacio
    # TODO: publicar PedidoCreado a EventBridge
    # TODO: retornar 201 con orderId
    return error(501, "Not implemented")
