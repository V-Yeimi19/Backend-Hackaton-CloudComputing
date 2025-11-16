import json
import os
import boto3

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
    print("Event resumenIncidentes:", json.dumps(event))

    try:
        res = incidentes_table.scan()
    except Exception as e:
        print("Error leyendo Incidentes:", e)
        return _response(500, {"message": "Error interno leyendo incidentes"})

    items = res.get("Items", [])

    por_estado = {}
    por_nivel = {}
    por_area = {}

    for it in items:
        est = it.get("estado", "DESCONOCIDO")
        niv = it.get("nivelDeGravedad", "DESCONOCIDO")
        area = it.get("areaResponsable", "DESCONOCIDO")

        por_estado[est] = por_estado.get(est, 0) + 1
        por_nivel[niv] = por_nivel.get(niv, 0) + 1
        por_area[area] = por_area.get(area, 0) + 1

    return _response(
        200,
        {
            "total": len(items),
            "porEstado": por_estado,
            "porNivelDeGravedad": por_nivel,
            "porAreaResponsable": por_area,
        },
    )
