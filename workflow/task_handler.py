from common.responses import ok
from common.dynamo import update_item
from common.events import put_event


def lambda_handler(event, context):
    # TODO: recibir { orderId, tenantId, source, step, taskToken } de la state machine
    # TODO: UpdateItem: guardar taskToken y currentStep en el pedido
    # TODO: publicar EstadoCambiado a EventBridge
    # TODO: retornar exito (la state machine espera respuesta)
    return {"statusCode": 200}
