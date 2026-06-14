import json
import os
import boto3
from common.responses import ok, error
from common.dynamo import get_item, update_item

stepfunctions = boto3.client("stepfunctions")


def lambda_handler(event, context):
    # TODO: extraer tenantId del authorizer context
    # TODO: extraer {id} de path params
    # TODO: GetItem orders para obtener taskToken y currentStep
    # TODO: llamar SendTaskSuccess con el taskToken
    # TODO: UpdateItem: avanzar currentStep, registrar endedAt en steps
    # TODO: si no hay taskToken, retornar 400
    return error(501, "Not implemented")
