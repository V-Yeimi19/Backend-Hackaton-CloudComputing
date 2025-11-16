import boto3
import json

def lambda_handler(event, context):
    try:
        # Debug: imprimir el evento completo
        print("Event recibido:", json.dumps(event))

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        import os
        table_name = os.environ.get('TABLE_HISTORIAL', 't_historial_incidentes')
        tabla_historial = dynamodb.Table(table_name)

        # Obtener todos los incidentes
        response = tabla_historial.scan()
        incidentes = response.get('Items', [])

        # Ordenar por fecha de creación (más recientes primero)
        # Usar createdAt en lugar de fecha_creacion
        incidentes.sort(key=lambda x: x.get('createdAt', ''), reverse=True)

        # Retornar lista completa de incidentes con toda su información
        return {
            'statusCode': 200,
            'body': {
                'total': len(incidentes),
                'incidentes': incidentes
            }
        }

    except Exception as e:
        # Excepción y retornar un código de error HTTP 500
        print("Exception:", str(e))
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
