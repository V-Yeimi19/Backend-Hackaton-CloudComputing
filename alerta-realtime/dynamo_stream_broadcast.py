import json
import os
import boto3
from boto3.dynamodb.types import TypeDeserializer

CONNECTIONS_TABLE = os.environ["CONNECTIONS_TABLE"]
WS_ENDPOINT = os.environ["WS_ENDPOINT"]
LAMBDA_GESTION_TRABAJADORES = os.environ.get("LAMBDA_GESTION_TRABAJADORES")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(CONNECTIONS_TABLE)

apigw = boto3.client(
    "apigatewaymanagementapi",
    endpoint_url=WS_ENDPOINT
)

lambda_client = boto3.client("lambda")

deserializer = TypeDeserializer()

def dynamodb_item_to_dict(item):
    if not item:
        return None
    return {k: deserializer.deserialize(v) for k, v in item.items()}

def lambda_handler(event, context):
    print("Stream event:", json.dumps(event))

    for record in event["Records"]:
        event_name = record["eventName"]  # INSERT, MODIFY, REMOVE

        new_image = record["dynamodb"].get("NewImage")
        old_image = record["dynamodb"].get("OldImage")

        new_item = dynamodb_item_to_dict(new_image)
        old_item = dynamodb_item_to_dict(old_image)

        # Si es un INSERT (nuevo reporte creado), invocar gestionTrabajadores automáticamente
        if event_name == "INSERT" and new_item and LAMBDA_GESTION_TRABAJADORES:
            reporte_id = new_item.get("id")
            estado = new_item.get("Estado")

            # Solo auto-asignar si el estado es "Notificado"
            if reporte_id and estado == "Notificado":
                print(f"Nuevo reporte detectado: {reporte_id}. Invocando auto-asignación de trabajador...")
                try:
                    payload = {
                        "body": json.dumps({
                            "id": reporte_id
                        })
                    }

                    response = lambda_client.invoke(
                        FunctionName=LAMBDA_GESTION_TRABAJADORES,
                        InvocationType="Event",  # Asíncrono
                        Payload=json.dumps(payload)
                    )

                    print(f"Lambda gestionTrabajadores invocada. StatusCode: {response['StatusCode']}")
                except Exception as e:
                    print(f"Error al invocar gestionTrabajadores: {str(e)}")
                    # No fallar el broadcasting si falla la asignación

        # Preparar mensaje para broadcasting
        message = {
            "eventName": event_name,
            "newImage": new_item,
            "oldImage": old_item
        }

        broadcast_to_all(message)

    return {
        "statusCode": 200,
        "body": "OK"
    }

def broadcast_to_all(message):
    payload = json.dumps(message).encode("utf-8")

    resp = table.scan(ProjectionExpression="connectionId")
    connections = resp.get("Items", [])

    print(f"Broadcasting to {len(connections)} connections")

    for item in connections:
        connection_id = item["connectionId"]

        try:
            apigw.post_to_connection(
                ConnectionId=connection_id,
                Data=payload
            )
        except apigw.exceptions.GoneException:
            print(f"Stale connection, deleting {connection_id}")
            table.delete_item(Key={"connectionId": connection_id})
        except Exception as e:
            print(f"Error sending to {connection_id}: {e}")