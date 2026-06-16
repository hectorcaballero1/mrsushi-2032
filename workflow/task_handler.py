import time
from common.dynamo import get_table
from common.events import put_event
from datetime import datetime, timezone

# Status que corresponde al INICIO de cada step (resume_step pone el status al cerrarlo)
STEP_TO_STATUS = {
    "cocina_fria": "cocinando",
    "cocina_caliente": "cocinando",
    "empacar": "empacando",
    "repartir": "repartiendo",
    "entregar_rappi": "entregando_a_rappi",
}


def lambda_handler(event, context):
    order_id = event["orderId"]
    tenant_id = event["tenantId"]
    source = event["source"]
    step = event["step"]
    task_token = event["taskToken"]

    new_status = STEP_TO_STATUS.get(step, step)
    now = int(time.time())
    created_at = datetime.now(timezone.utc).isoformat()

    pk = f"TENANT#{tenant_id}"
    sk = f"ORDER#{order_id}"

    table = get_table("ORDERS_TABLE")
    # SET steps.<step> = {startedAt} — funciona porque crear_pedido inicializa steps: {}
    # SET taskTokens.<step> = token — permite tener 2 tokens activos durante el Parallel de Cocinar
    table.update_item(
        Key={"PK": pk, "SK": sk},
        UpdateExpression=(
            "SET #status = :status, #gsi2pk = :gsi2pk, "
            "#steps.#step = :step_data, #taskTokens.#step = :token, "
            "#currentStep = :step"
        ),
        ExpressionAttributeNames={
            "#status": "status",
            "#gsi2pk": "GSI2PK",
            "#steps": "steps",
            "#step": step,
            "#taskTokens": "taskTokens",
            "#currentStep": "currentStep",
        },
        ExpressionAttributeValues={
            ":status": new_status,
            ":gsi2pk": f"TENANT#{tenant_id}#STATUS#{new_status}",
            ":step_data": {},
            ":token": task_token,
            ":step": step,
        },
    )

    put_event("mrsushi.workflow", "EstadoCambiado", {
        "orderId": order_id,
        "tenantId": tenant_id,
        "source": source,
        "step": step,
        "status": new_status,
    })

    # La state machine NO espera el return de esta Lambda (el flujo continúa con
    # waitForTaskToken). Devolvemos algo limpio por si acaso.
    return {"ok": True}
