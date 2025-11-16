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
        incidente_id = body.get('id')
        nuevo_status = body.get('status')
        resolved_by = body.get('resolvedBy')  # Opcional, solo cuando status = 'Finalizado'

        # Validar campos obligatorios
        if not all([incidente_id, nuevo_status]):
            return {
                'statusCode': 400,
                'body': {
                    'error': 'Faltan campos requeridos: id, status'
                }
            }

        # Validar estados permitidos
        estados_validos = ['Notificado', 'En Proceso', 'Finalizado']
        if nuevo_status not in estados_validos:
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

        # Fecha y hora actual en formato ISO
        updated_at = datetime.now().isoformat()

        # Preparar la expresión de actualización
        update_expression = 'SET #status = :status, updatedAt = :updated_at'
        expression_attribute_values = {
            ':status': nuevo_status,
            ':updated_at': updated_at
        }
        expression_attribute_names = {
            '#status': 'status'
        }

        # Si el estado es "Finalizado", agregar resolvedAt y resolvedBy
        if nuevo_status == 'Finalizado':
            update_expression += ', resolvedAt = :resolved_at'
            expression_attribute_values[':resolved_at'] = updated_at

            if resolved_by:
                update_expression += ', resolvedBy = :resolved_by'
                expression_attribute_values[':resolved_by'] = resolved_by

        # Actualizar el incidente
        tabla_historial.update_item(
            Key={'id': incidente_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names
        )

        # Retornar éxito
        response_body = {
            'message': 'Incidente actualizado exitosamente',
            'id': incidente_id,
            'status': nuevo_status,
            'updatedAt': updated_at
        }

        if nuevo_status == 'Finalizado':
            response_body['resolvedAt'] = updated_at
            if resolved_by:
                response_body['resolvedBy'] = resolved_by

        return {
            'statusCode': 200,
            'body': response_body
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
