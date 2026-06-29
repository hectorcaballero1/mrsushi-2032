STEP_TO_ALLOWED_ROLES = {
    "tomar_orden":      ["cocinero", "admin"],
    "revisar_despacho": ["despachador", "admin"],
    "cocina_fria":    ["cocinero", "admin"],
    "cocina_caliente": ["cocinero", "admin"],
    "empacar":        ["despachador", "admin"],
    "repartir":       ["delivery", "admin"],
    "entregar_rappi": ["despachador", "admin"],
}


def require_role(claims: dict, allowed: list) -> bool:
    return claims.get("role") in allowed
