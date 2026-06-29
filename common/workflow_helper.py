import json
import time
import boto3
from common.dynamo import get_table
from boto3.dynamodb.conditions import Key

stepfunctions = boto3.client("stepfunctions")


def get_order_by_external_ref(external_ref):
    """Query GSI3 (sparse, solo pedidos rappi) por externalRef."""
    table = get_table("ORDERS_TABLE")
    items = table.query(
        IndexName="GSI3",
        KeyConditionExpression=Key("GSI3PK").eq(external_ref),
    ).get("Items", [])
    return items[0] if items else None


def resume_step(order, step, by=None, extra_output=None):
    """
    Reanuda el workflow de Step Functions para el step dado y actualiza el pedido.

    - Lee taskTokens[step] del pedido ya cargado.
    - Llama SendTaskSuccess con el token (el output lleva orderId/tenantId/source para
      que los estados siguientes conserven el contexto; extra_output agrega campos de
      decisión humana como decision/motivo para los Choice de admisión/revisión).
    - Actualiza en DynamoDB: status, steps[step].endedAt (y .by si se pasa),
      y elimina el token consumido de taskTokens.

    Lanza ValueError si no hay token para el step indicado.
    """
    task_tokens = order.get("taskTokens", {})
    token = task_tokens.get(step)
    if not token:
        raise ValueError(f"No hay taskToken activo para el step '{step}'")

    # Status al COMPLETAR cada step (task_handler pone el status al empezar)
    STEP_TO_STATUS = {
        "tomar_orden": "recibido",       # el Choice posterior decide a dónde va
        "revisar_despacho": "en_revision",
        "cocina_fria": "cocinando",      # el otro branch puede seguir activo
        "cocina_caliente": "cocinando",
        "empacar": "empacando",          # task_handler(repartir/entregar_rappi) lo sigue
        "repartir": "entregado",
        "entregar_rappi": "entregado",
    }
    new_status = STEP_TO_STATUS.get(step, step)
    now = int(time.time())

    # El output que recibe el siguiente estado de SF debe tener orderId/tenantId/source
    sf_output = {
        "orderId": order.get("SK", "").removeprefix("ORDER#"),
        "tenantId": order.get("PK", "").removeprefix("TENANT#"),
        "source": order.get("source", "web"),
    }
    if extra_output:
        sf_output.update(extra_output)
    stepfunctions.send_task_success(
        taskToken=token,
        output=json.dumps(sf_output),
    )

    pk = order["PK"]
    sk = order["SK"]

    # update_item de common/dynamo no soporta REMOVE ni paths anidados,
    # así que construimos la expresión directamente.
    table = get_table("ORDERS_TABLE")
    tenant_id = pk.removeprefix("TENANT#")
    set_parts = [
        "#status = :status",
        "#gsi2pk = :gsi2pk",
        "#steps.#step_name.#endedAt = :endedAt",
    ]
    names = {
        "#status": "status",
        "#gsi2pk": "GSI2PK",
        "#steps": "steps",
        "#step_name": step,
        "#endedAt": "endedAt",
        "#taskTokens": "taskTokens",
        "#step_token": step,
    }
    values = {
        ":status": new_status,
        ":gsi2pk": f"TENANT#{tenant_id}#STATUS#{new_status}",
        ":endedAt": now,
    }

    if by:
        set_parts.append("#steps.#step_name.#by = :by")
        names["#by"] = "by"
        values[":by"] = by

    table.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression="SET " + ", ".join(set_parts) + " REMOVE #taskTokens.#step_token",
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )
