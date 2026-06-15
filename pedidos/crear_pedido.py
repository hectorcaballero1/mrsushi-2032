import uuid
import json
from decimal import Decimal
from datetime import datetime, timezone
from common.responses import created, error
from common.dynamo import put_item
from common.events import put_event
from common.kitchen_stations import CATEGORY_TO_STATION


def _calc_cocinas(items):
    tiene_fria = tiene_caliente = False
    for item in items:
        station = CATEGORY_TO_STATION.get(item.get("category", ""))
        if station in ("fria", "ambas"):
            tiene_fria = True
        if station in ("caliente", "ambas"):
            tiene_caliente = True
    # Fallback: pedido solo de bebidas/salsas/merch → pasa igual por un checkpoint
    if not tiene_fria and not tiene_caliente:
        tiene_fria = True
    return tiene_fria, tiene_caliente


def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")

    tenant_id = body.get("tenantId", "").strip()
    source = body.get("source", "web")
    # Convertir floats a Decimal — DynamoDB no acepta float
    items = json.loads(json.dumps(body.get("items", [])), parse_float=Decimal)
    customer = body.get("customer", {})
    external_ref = body.get("externalRef")  # solo para source=rappi
    customer_id = body.get("customerId")    # opcional para source=web

    if not tenant_id:
        return error(400, "tenantId required")
    if not items:
        return error(400, "items required")
    if source == "rappi" and not external_ref:
        return error(400, "externalRef required for rappi orders")

    order_id = str(uuid.uuid4())
    tiene_fria, tiene_caliente = _calc_cocinas(items)
    total = sum(item.get("price", 0) * item.get("qty", 1) for item in items)
    created_at = datetime.now(timezone.utc).isoformat()
    status = "recibido"

    item = {
        "PK": f"TENANT#{tenant_id}",
        "SK": f"ORDER#{order_id}",
        # GSI2: cola FIFO por tenant+status
        "GSI2PK": f"TENANT#{tenant_id}#STATUS#{status}",
        "GSI2SK": created_at,
        "source": source,
        "status": status,
        "total": str(total),
        "items": items,
        "customer": customer,
        "createdAt": created_at,
        # steps: {} inicializado vacío para que los SET anidados de task_handler no fallen
        "steps": {},
        "taskTokens": {},
        "tieneFria": tiene_fria,
        "tieneCaliente": tiene_caliente,
    }

    if external_ref:
        item["externalRef"] = external_ref
        # GSI3: sparse, solo pedidos rappi — permite lookup por externalRef
        item["GSI3PK"] = external_ref

    # customerId es opcional y viene del body sin verificación JWT (guest checkout +
    # Rappi no tienen authorizer). El control real vive en GET /orders?mine=true,
    # que sí exige token y usa el userId verificado de los claims.
    if customer_id:
        item["GSI1PK"] = f"CUSTOMER#{customer_id}"
        item["GSI1SK"] = created_at

    put_item("ORDERS_TABLE", item)

    put_event("mrsushi.pedidos", "PedidoCreado", {
        "orderId": order_id,
        "tenantId": tenant_id,
        "source": source,
        "tieneFria": tiene_fria,
        "tieneCaliente": tiene_caliente,
    })

    return created({"orderId": order_id, "status": status})
