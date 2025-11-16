import boto3
import hashlib
import json
import uuid
import re

# Hashear contraseña
def hash_password(password):
    # Retorna la contraseña hasheada
    return hashlib.sha256(password.encode()).hexdigest()

# Validar correo institucional UTEC
def validar_correo_utec(correo):
    # Valida que el correo termine con @utec.edu.pe
    patron = r'^[a-zA-Z0-9._%+-]+@utec\.edu\.pe$'
    return re.match(patron, correo) is not None

# Validar área de trabajo según el rol
def validar_area_trabajo(role, area_trabajo):
    areas_validas = [
        'Bienestar Estudiantil',
        'Counter Alumnos',
        'Limpieza',
        'Seguridad',
        'Servicios Financieros',
        'Defensoría Universitaria',
        'Mantenimiento e Infraestructura',
        'Tecnologías de la Información',
        'Servicios Generales',
        'Biblioteca',
        'Encargado de Laboratorio'
    ]

    if role == 'Estudiante':
        return area_trabajo == 'student'
    elif role == 'Trabajador':
        return area_trabajo in areas_validas
    else:
        return False

# Función que maneja el registro de usuario
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
        nombre_completo = body.get('nombre_completo')
        correo = body.get('correo')
        password = body.get('password')
        role = body.get('role')
        area_trabajo = body.get('area_trabajo')

        # Validar campos básicos (area_trabajo es opcional para Estudiantes)
        if not all([nombre_completo, correo, password, role]):
            return {
                'statusCode': 400,
                'body': {
                    'error': 'Faltan campos requeridos: nombre_completo, correo, password, role'
                }
            }

        # Si es Estudiante y no se especifica area_trabajo, asignar "student" por defecto
        if role == 'Estudiante' and not area_trabajo:
            area_trabajo = 'student'

        # Si es Trabajador, area_trabajo es obligatorio
        if role == 'Trabajador' and not area_trabajo:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'El campo area_trabajo es obligatorio para trabajadores'
                }
            }

        # Validar correo institucional
        if not validar_correo_utec(correo):
            return {
                'statusCode': 400,
                'body': {
                    'error': 'El correo debe ser institucional de UTEC (@utec.edu.pe)'
                }
            }

        # Validar role
        if role not in ['Estudiante', 'Trabajador']:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'El role debe ser "Estudiante" o "Trabajador"'
                }
            }

        # Validar área de trabajo según el rol
        if not validar_area_trabajo(role, area_trabajo):
            if role == 'Estudiante':
                return {
                    'statusCode': 400,
                    'body': {
                        'error': 'Los estudiantes deben tener área_trabajo = "student"'
                    }
                }
            else:
                return {
                    'statusCode': 400,
                    'body': {
                        'error': 'Área de trabajo no válida para trabajadores'
                    }
                }

        # Conectar DynamoDB
        dynamodb = boto3.resource('dynamodb')
        import os
        table_name = os.environ.get('TABLE_USUARIOS', 't_usuarios_hack')
        t_usuarios = dynamodb.Table(table_name)

        # Verificar si el usuario ya existe
        response = t_usuarios.get_item(Key={'correo': correo})
        if 'Item' in response:
            return {
                'statusCode': 400,
                'body': {
                    'error': 'El usuario ya está registrado con este correo'
                }
            }

        # Generar UUID automático
        user_uuid = str(uuid.uuid4())

        # Hashear la contraseña
        hashed_password = hash_password(password)

        # Almacenar los datos del usuario en DynamoDB
        t_usuarios.put_item(
            Item={
                'correo': correo,  # Partition key
                'user_id': user_uuid,
                'nombre_completo': nombre_completo,
                'password': hashed_password,
                'role': role,
                'area_trabajo': area_trabajo
            }
        )

        # Retornar éxito
        return {
            'statusCode': 200,
            'body': {
                'message': 'Usuario registrado exitosamente',
                'user_id': user_uuid,
                'correo': correo,
                'nombre_completo': nombre_completo,
                'role': role,
                'area_trabajo': area_trabajo
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