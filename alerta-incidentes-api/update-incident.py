# update_incidente.py
import json
import os
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

INCIDENTES_TABLE = os.environ["INCIDENTES_TABLE"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(INCIDENTES_TABLE)

def lambda_handler(event, context):
    print("Event actualizarEstadoIncidente:", json.dumps(event))

    # id del path: /incidentes/{id}/estado
    incident_id = event.get("pathParameters", {}).get("id")

    if not incident_id:
        return _response(400, {"message": "Falta el id en la URL"})

    # Body con JSON: { "estado": "EN_ATENCION" }
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"message": "Body debe ser JSON"})

    nuevo_estado = body.get("estado")

    if not nuevo_estado:
        return _response(400, {"message": "Falta el campo 'estado' en el body"})

    now = datetime.utcnow().isoformat()

    try:
        resp = table.update_item(
            Key={"id": incident_id},
            UpdateExpression="SET estado = :e, updatedAt = :u",
            ExpressionAttributeValues={
                ":e": nuevo_estado,
                ":u": now,
            },
            ConditionExpression="attribute_exists(id)",  # solo si existe
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return _response(404, {"message": "Incidente no encontrado"})
        print("Error actualizando incidente:", e)
        return _response(500, {"message": "Error actualizando incidente"})

    item_actualizado = resp.get("Attributes", {})

    return _response(200, {
        "message": "Estado actualizado",
        "incidente": item_actualizado,
    })

def _response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }