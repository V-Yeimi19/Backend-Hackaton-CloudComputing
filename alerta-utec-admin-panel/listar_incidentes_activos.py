import json
import os
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource("dynamodb")
INCIDENTES_TABLE = os.environ["INCIDENTES_TABLE"]
incidentes_table = dynamodb.Table(INCIDENTES_TABLE)


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    print("Event listarIncidentesActivos:", json.dumps(event))

    params = (event.get("queryStringParameters") or {}) or {}
    estado = params.get("estado")
    nivel = params.get("nivelDeGravedad")
    area = params.get("areaResponsable")

    # Para hackathon: usamos Scan + filtro. Si tuvieras MUCHOS datos,
    # aquí ya pensaríamos en GSIs.
    filtro = Attr("id").exists()

    # Por defecto, mostrar solo incidentes NO cerrados
    if estado:
        filtro = filtro & Attr("estado").eq(estado)
    else:
        filtro = filtro & Attr("estado").ne("Cerrado")

    if nivel:
        filtro = filtro & Attr("nivelDeGravedad").eq(nivel)

    if area:
        filtro = filtro & Attr("areaResponsable").eq(area)

    try:
        res = incidentes_table.scan(
            FilterExpression=filtro
        )
    except Exception as e:
        print("Error leyendo Incidentes:", e)
        return _response(500, {"message": "Error interno leyendo incidentes"})

    items = res.get("Items", [])

    # Si quieres priorizar en el panel:
    # ordenar por nivelDeGravedad y/o createdAt en memoria
    # Ejemplo simple: primero Alta, luego Media, luego Baja
    prioridad = {"Alta": 1, "Media": 2, "Baja": 3}

    def prioridad_key(x):
        return (
            prioridad.get(x.get("nivelDeGravedad"), 99),
            x.get("createdAt", ""),
        )

    items.sort(key=prioridad_key)

    return _response(
        200,
        {
            "items": items,
            "count": len(items),
        },
    )
