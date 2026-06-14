import json
from common.responses import created, error
from common.dynamo import put_item


def lambda_handler(event, context):
    # TODO: parsear body, validar datos
    # TODO: hashear password con hashlib.sha256 (o bcrypt si se agrega)
    # TODO: si role=customer => PK=BRAND#mrsushi, si worker => PK=TENANT#<sede>
    # TODO: guardar en users table
    # TODO: retornar 201 con userId
    return error(501, "Not implemented")
