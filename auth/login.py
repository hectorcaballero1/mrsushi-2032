import json
from common.responses import ok, error
from common.dynamo import get_item
from common.jwt_helper import emit_token


def lambda_handler(event, context):
    # TODO: parsear email, password, role (customer vs worker)
    # TODO: determinar PK segun role (BRAND#mrsushi o TENANT#<sede>)
    # TODO: GetItem en users, validar password hash
    # TODO: emitir JWT con sub=userId, role, tenantId (si worker)
    # TODO: retornar { token }
    return error(501, "Not implemented")
