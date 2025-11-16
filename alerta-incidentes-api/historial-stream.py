# historial_stream.py
import json
import os
import boto3
from boto3.dynamodb.types import TypeDeserializer
from datetime import datetime

INCIDENTES_TABLE = os.environ["INCIDENTES_TABLE"]   # no lo usamos directamente, pero lo dejamos por claridad
HISTORIAL_TABLE = os.environ["HISTORIAL_TABLE"]

dynamodb = boto3.resource("dynamodb")
historial_table = dynamodb.Table(HISTORIAL_TABLE)

deserializer = TypeDeserializer()

def _to_dict(item):
    if not item:
        return None
    return {k: deserializer.deserialize(v) for k, v in item.items()}

def lambda_handler(event, context):
    print("Stream event historial_stream:", json.dumps(event))

    for record in event["Records"]:
        event_name = record["eventName"]  # INSERT, MODIFY, REMOVE
        new_image = _to_dict(record["dynamodb"].get("NewImage"))
        old_image = _to_dict(record["dynamodb"].get("OldImage"))

        if event_name == "INSERT":
            # Log inicial del incidente
            _registrar_historial(new_item=new_image, motivo="CREADO")

        elif event_name == "MODIFY":
            # Solo registramos si cambió el estado
            nuevo_estado = (new_image or {}).get("estado")
            estado_anterior = (old_image or {}).get("estado")

            if nuevo_estado != estado_anterior:
                _registrar_historial(new_item=new_image, motivo="CAMBIO_ESTADO")

        # Para REMOVE podrías guardar un log también si quieres

    return {
        "statusCode": 200,
        "body": "OK"
    }

def _registrar_historial(new_item, motivo):
    if not new_item:
        return

    incidente_id = new_item.get("id")
    estado = new_item.get("estado")
    now = datetime.utcnow().isoformat()

    # Item acorde a la tabla t_historial: PK + SK
    item_historial = {
        "incidenteId": incidente_id,  # Partition key
        "changedAt": now,             # Sort key
        "estado": estado,
        "motivo": motivo,
    }

    print("Guardando en historial:", item_historial)

    historial_table.put_item(Item=item_historial)