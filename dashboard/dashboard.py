from common.responses import ok, error


def lambda_handler(event, context):
    # TODO: contar pedidos por status (cola actual), tiempos promedio por paso
    # TODO: solo admin puede acceder (validar role del authorizer context)
    # TODO: retornar stats: { porStatus: {...}, tiempos: {...} }
    return error(501, "Not implemented")
