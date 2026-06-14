# Fuente única de verdad para el mapeo categoría → estación de cocina.
# Importado por seed/seed_catalog.py y pedidos/crear_pedido.py.
#
# Valores: "fria" | "caliente" | "ambas" | None
#   "ambas" → combos que mezclan ambas estaciones
#   None    → sin estación (bebidas, salsas, merch)

CATEGORY_TO_STATION: dict[str, str | None] = {
    "Promociones": "ambas",
    "Promos de la Semana": "ambas",
    "Boxes": "fria",
    "Poke": "fria",
    "Makis": "fria",
    "Entradas Frías": "fria",
    "Entradas Calientes": "caliente",
    "Temakis": "fria",
    "Alitas": "caliente",
    "Los favoritos de Neki": "fria",
    "Meshi": "caliente",
    "Sandwich Sushi": "fria",
    "Los Fusionados": "caliente",
    "Bocaditos (Fusionados)": "caliente",
    "Sopas (Fusionados)": "caliente",
    "Banquetes": "ambas",
    "Salsa": None,
    "Bebidas": None,
    "Merch": None,
}
