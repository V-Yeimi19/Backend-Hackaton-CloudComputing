import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    try:
        # Debug: imprimir el evento completo
        print("Event recibido:", json.dumps(event))

        # Parse del body si viene como string JSON
        if 'body' in event and event['body']:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            # Si no hay body, asumir que el event es el body directamente
            body = event

        # Debug: imprimir el body parseado
        print("Body parseado:", body)

        # Obtener los campos requeridos
        incidente_id = body.get('incidente_id')
        nuevo_estado = body.get('estado')
        comentario = body.get('comentario', '')  # Opcional

        # Validar campos obligatorios
        if not all([incidente_id, nuevo_estado]):
            return {
                'statusCode': 400,
                'body': {
                    'error': 'Faltan campos requeridos: incidente_id, estado'
                }
            }

        # Validar estados permitidos
        estados_validos = ['notificado', 'en_proceso', 'resuelto']
        if nuevo_estado not in estados_validos:
            return {
                'statusCode': 400,
                'body': {
                    'error': f'Estado no válido. Debe ser uno de: {", ".join(estados_validos)}'
                }
            }

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        import os
        table_name = os.environ.get('TABLE_HISTORIAL', 't_historial_incidentes')
        tabla_historial = dynamodb.Table(table_name)

        # Obtener el incidente actual
        response = tabla_historial.get_item(Key={'id': incidente_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': {
                    'error': 'Incidente no encontrado'
                }
            }

        incidente = response['Item']

        # Fecha y hora actual
        fecha_actualizacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Crear nueva entrada en el historial de estados
        nueva_entrada_historial = {
            'estado': nuevo_estado,
            'fecha': fecha_actualizacion,
            'comentario': comentario or f'Estado cambiado a {nuevo_estado}'
        }

        # Obtener el historial actual y agregar la nueva entrada
        historial_estados = incidente.get('historial_estados', [])
        historial_estados.append(nueva_entrada_historial)

        # Actualizar el incidente
        tabla_historial.update_item(
            Key={'id': incidente_id},
            UpdateExpression='SET estado = :estado, fecha_actualizacion = :fecha, historial_estados = :historial',
            ExpressionAttributeValues={
                ':estado': nuevo_estado,
                ':fecha': fecha_actualizacion,
                ':historial': historial_estados
            }
        )

        # Retornar éxito
        return {
            'statusCode': 200,
            'body': {
                'message': 'Incidente actualizado exitosamente',
                'incidente_id': incidente_id,
                'nuevo_estado': nuevo_estado,
                'fecha_actualizacion': fecha_actualizacion
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
