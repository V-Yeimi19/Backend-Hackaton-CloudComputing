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
        print("Body parseado:", json.dumps(body))

        # Obtener token del body o del header Authorization
        token = body.get('token')

        # Si no está en el body, buscar en headers
        if not token and event.get('headers'):
            auth_header = event['headers'].get('Authorization') or event['headers'].get('authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '')

        # Validar que el token existe
        if not token:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Token no proporcionado. Envíalo en el body o en el header Authorization'
                })
            }

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        import os
        table_tokens_name = os.environ.get('TABLE_TOKENS', 't_tokens_acceso')
        table = dynamodb.Table(table_tokens_name)

        # Buscar el token en la tabla
        response = table.get_item(Key={'token': token})

        if 'Item' not in response:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Token inválido',
                    'valid': False
                })
            }

        # Obtener datos del token
        token_data = response['Item']
        expires = token_data['expires']

        # Verificar si el token ha expirado
        fecha_expiracion = datetime.strptime(expires, '%Y-%m-%d %H:%M:%S')
        fecha_actual = datetime.now()

        if fecha_actual > fecha_expiracion:
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Token expirado',
                    'valid': False,
                    'expired': True
                })
            }

        # Obtener información del usuario
        table_usuarios_name = os.environ.get('TABLE_USUARIOS', 't_usuarios_hack')
        table_usuarios = dynamodb.Table(table_usuarios_name)
        user_response = table_usuarios.get_item(Key={'correo': token_data['correo']})

        if 'Item' not in user_response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'Usuario no encontrado',
                    'valid': False
                })
            }

        user_data = user_response['Item']

        # Token válido y activo
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Token válido',
                'valid': True,
                'user': {
                    'user_id': user_data['user_id'],
                    'correo': user_data['correo'],
                    'nombre_completo': user_data['nombre_completo'],
                    'role': user_data['role'],
                    'area_trabajo': user_data['area_trabajo']
                },
                'token_expires': expires
            })
        }

    except Exception as e:
        # Excepción y retornar un código de error HTTP 500
        print("Exception:", str(e))
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e),
                'valid': False
            })
        }
