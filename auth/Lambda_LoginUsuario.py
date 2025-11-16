import boto3
import hashlib
import json
import uuid
import re
from datetime import datetime, timedelta

# Hashear contraseña
def hash_password(password):
    # Retorna la contraseña hasheada
    return hashlib.sha256(password.encode()).hexdigest()

# Validar correo institucional UTEC
def validar_correo_utec(correo):
    # Valida que el correo termine con @utec.edu.pe
    patron = r'^[a-zA-Z0-9._%+-]+@utec\.edu\.pe$'
    return re.match(patron, correo) is not None

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

        # Obtener correo y password
        correo = body.get('correo')
        password = body.get('password')

        # Validar que los campos existen
        if not correo or not password:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Faltan campos requeridos: correo y password'
                })
            }

        # Validar correo institucional
        if not validar_correo_utec(correo):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'El correo debe ser institucional de UTEC (@utec.edu.pe)'
                })
            }

        # Hashear la contraseña ingresada
        hashed_password = hash_password(password)

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        import os
        table_name = os.environ.get('TABLE_USUARIOS', 't_usuarios_hack')
        table = dynamodb.Table(table_name)

        # Buscar usuario por correo
        response = table.get_item(Key={'correo': correo})

        if 'Item' not in response:
            return {
                'statusCode': 403,
                'body': json.dumps({
                    'error': 'Usuario no existe'
                })
            }

        # Verificar contraseña
        user_data = response['Item']
        hashed_password_bd = user_data['password']

        if hashed_password != hashed_password_bd:
            return {
                'statusCode': 403,
                'body': json.dumps({
                    'error': 'Contraseña incorrecta'
                })
            }

        # Generar token de acceso
        token = str(uuid.uuid4())
        fecha_hora_exp = datetime.now() + timedelta(minutes=60)

        # Almacenar token en tabla de tokens
        registro_token = {
            'token': token,
            'correo': correo,
            'user_id': user_data['user_id'],
            'expires': fecha_hora_exp.strftime('%Y-%m-%d %H:%M:%S')
        }

        table_tokens_name = os.environ.get('TABLE_TOKENS', 't_tokens_acceso')
        table_tokens = dynamodb.Table(table_tokens_name)
        table_tokens.put_item(Item=registro_token)

        # Retornar éxito con información del usuario
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Login exitoso',
                'token': token,
                'expires': registro_token['expires'],
                'user': {
                    'user_id': user_data['user_id'],
                    'correo': user_data['correo'],
                    'nombre_completo': user_data['nombre_completo'],
                    'role': user_data['role'],
                    'area_trabajo': user_data['area_trabajo']
                }
            })
        }

    except Exception as e:
        # Excepción y retornar un código de error HTTP 500
        print("Exception:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }