import boto3
import json
import os

def lambda_handler(event, context):
    """
    Lambda para obtener el historial de todos los incidentes.
    Lee desde la tabla TABLE_INCIDENTES y retorna todos los incidentes ordenados por fecha.
    """
    try:
        # Debug: imprimir el evento completo
        print("Event recibido:", json.dumps(event))

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        tabla_incidentes = dynamodb.Table(os.environ['TABLE_INCIDENTES'])

        # Obtener todos los incidentes
        response = tabla_incidentes.scan()
        incidentes = response.get('Items', [])

        # Ordenar por fecha de creación (más recientes primero)
        # Usar FechaCreacion que es el campo correcto en la tabla
        incidentes.sort(key=lambda x: x.get('FechaCreacion', ''), reverse=True)

        print(f"Total de incidentes encontrados: {len(incidentes)}")

        # Retornar lista completa de incidentes con toda su información
        return {
            'statusCode': 200,
            'body': json.dumps({
                'total': len(incidentes),
                'incidentes': incidentes
            })
        }

    except Exception as e:
        # Excepción y retornar un código de error HTTP 500
        print("Exception:", str(e))
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
