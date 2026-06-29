import os
import json
import urllib.request
import urllib.error
from common.dynamo import get_item

STEP_TO_STATUS = {
    "tomar_orden": "recibido",
    "revisar_despacho": "en_revision",
    "cocina_fria": "cocinando",
    "cocina_caliente": "cocinando",
    "empacar": "empacando",
    "repartir": "repartiendo",
    "entregar_rappi": "entregando_a_rappi",
}


def lambda_handler(event, context):
    detail = event.get("detail", {})
    order_id = detail.get("orderId")
    tenant_id = detail.get("tenantId")
    step = detail.get("step")

    if not order_id or not tenant_id:
        return {"statusCode": 400}

    order = get_item("ORDERS_TABLE", f"TENANT#{tenant_id}", f"ORDER#{order_id}")
    if not order:
        return {"statusCode": 404}

    external_ref = order.get("externalRef")
    if not external_ref:
        return {"statusCode": 200}

    business_status = STEP_TO_STATUS.get(step, step)
    url = f"{os.environ['RAPPI_API_URL']}/orders/{external_ref}/status"
    body = json.dumps({"status": business_status}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": os.environ.get("RAPPI_WEBHOOK_SECRET", ""),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(
                f"Rappi notificado (order={order_id}, step={step}, "
                f"status={business_status}) → {resp.status} {resp.read()[:200]}"
            )
    except urllib.error.HTTPError as e:
        # HTTPError (401, 404, etc.) es subclase de URLError; logueamos el cuerpo
        print(
            f"Error HTTP notificando a Rappi (order={order_id}, step={step}, "
            f"url={url}): {e.code} {e.read()[:200]}"
        )
    except urllib.error.URLError as e:
        # Fallo de red/TLS/host inalcanzable (esquema https vs http, firewall, etc.)
        print(
            f"Error de red notificando a Rappi (order={order_id}, step={step}, "
            f"url={url}): {e.reason}"
        )

    return {"statusCode": 200}
