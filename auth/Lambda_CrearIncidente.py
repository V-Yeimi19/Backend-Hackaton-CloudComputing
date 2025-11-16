import boto3
import json
import uuid
from datetime import datetime

def calcular_prioridad(severity):
    """Calcula la prioridad numérica basada en la severidad"""
    prioridades = {
        'Leve': 1,
        'Moderado': 2,
        'Grave': 3
    }
    return prioridades.get(severity, 2)

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

        # Obtener los campos requeridos según la nueva estructura
        user_id = body.get('userId')
        description = body.get('description')
        category = body.get('category')
        severity = body.get('severity')
        location = body.get('location')
        assigned_area = body.get('assignedArea')

        # Validar campos obligatorios
        if not all([user_id, description, category, severity, location, assigned_area]):
            return {
                'statusCode': 400,
                'body': {
                    'error': 'Faltan campos requeridos: userId, description, category, severity, location, assignedArea'
                }
            }

        # Validar severity
        if severity not in ['Leve', 'Moderado', 'Grave']:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'La severidad debe ser: Leve, Moderado o Grave'
                }
            }

        # Generar ID único para el incidente
        incidente_id = str(uuid.uuid4())

        # Fecha y hora actual en formato ISO
        now = datetime.now()
        created_at = now.isoformat()

        # Calcular prioridad automática basada en severidad
        priority = calcular_prioridad(severity)

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        import os
        table_name = os.environ.get('TABLE_HISTORIAL', 't_historial_incidentes')
        tabla_historial = dynamodb.Table(table_name)

        # Crear registro del incidente con la estructura correcta
        incidente = {
            'id': incidente_id,
            'userId': user_id,
            'description': description,
            'category': category,
            'severity': severity,
            'location': location,
            'assignedArea': assigned_area,
            'status': 'Notificado',  # Estado inicial
            'createdAt': created_at,
            'updatedAt': created_at,
            'priority': priority
        }

        # Guardar en DynamoDB
        tabla_historial.put_item(Item=incidente)

        # Retornar éxito
        return {
            'statusCode': 201,
            'body': {
                'message': 'Incidente creado exitosamente',
                'incidente': incidente
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
