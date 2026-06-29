import json
import time
from botocore.exceptions import ClientError
from common.responses import ok, error
from common.dynamo import get_item, get_table
from common.workflow_helper import resume_step
from common.authz import STEP_TO_ALLOWED_ROLES, require_role

# Paso de revisión: el despachador CANCELA el pedido o lo RE-ENVÍA a cocina.
STEP = "revisar_despacho"


def _claim(order, user_id):
    """Escritura condicional anti-race: el primero que reclama la revisión gana."""
    table = get_table("ORDERS_TABLE")
    now = int(time.time())
    table.update_item(
        Key={"PK": order["PK"], "SK": order["SK"]},
        UpdateExpression="SET #steps.#step.#startedAt = :v, #steps.#step.#takenBy = :by",
        ConditionExpression="attribute_not_exists(#steps.#step.#startedAt)",
        ExpressionAttributeNames={
            "#steps": "steps",
            "#step": STEP,
            "#startedAt": "startedAt",
            "#takenBy": "takenBy",
        },
        ExpressionAttributeValues={":v": now, ":by": user_id or ""},
    )


def lambda_handler(event, context):
    claims = event.get("requestContext", {}).get("authorizer", {})
    tenant_id = claims.get("tenantId")
    user_id = claims.get("userId")

    if not tenant_id:
        return error(403, "tenantId missing from token")
    if not require_role(claims, STEP_TO_ALLOWED_ROLES[STEP]):
        return error(403, "rol no autorizado para revisar pedidos")

    order_id = event.get("pathParameters", {}).get("id")
    if not order_id:
        return error(400, "Missing order id")

    body = json.loads(event.get("body") or "{}")
    decision = body.get("decision")
    if decision not in ("cancelar", "reenviar"):
        return error(400, "decision debe ser 'cancelar' o 'reenviar'")
    motivo = (body.get("motivo") or "").strip()

    order = get_item("ORDERS_TABLE", f"TENANT#{tenant_id}", f"ORDER#{order_id}")
    if not order:
        return error(404, "Order not found")

    # El token de revisar_despacho lo crea taskHandler al entrar a ese estado (tras derivar).
    if not order.get("taskTokens", {}).get(STEP):
        return error(409, "La revisión aún no está lista, reintentá en unos segundos")

    try:
        _claim(order, user_id)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return error(409, "Este pedido ya está siendo revisado por otro trabajador")
        raise

    # cancelar -> ChoiceRevision va a MarcarCancelado; reenviar -> NecesitaCocina (Cocinar)
    extra = {"decision": decision}
    if motivo:
        extra["motivo"] = motivo
    try:
        resume_step(order, STEP, by=user_id, extra_output=extra)
    except ValueError as e:
        return error(400, str(e))

    return ok({"orderId": order_id, "decision": decision})
