import boto3
import json
import uuid
import os
from datetime import datetime

def lambda_handler(event, context):
    """
    Lambda para crear un nuevo incidente en la tabla de DynamoDB.

    Campos esperados en el body:
    - UsuarioId: ID del usuario que reporta el incidente
    - DescripcionCorta: Descripción breve del incidente
    - Categoria: Tipo de incidente (Fugas, Calidad del Inmobiliario, etc.)
    - Gravedad: Nivel de gravedad ('debil', 'moderado', 'fuerte')
    - Lugar: Ubicación específica del incidente
    """
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
            body = event

        print("Body parseado:", body)

        # Obtener los campos requeridos
        usuario_id = body.get('UsuarioId')
        descripcion_corta = body.get('DescripcionCorta')
        categoria = body.get('Categoria')
        gravedad = body.get('Gravedad')
        lugar = body.get('Lugar')

        # Validar campos obligatorios
        if not all([usuario_id, descripcion_corta, categoria, gravedad, lugar]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Faltan campos requeridos: UsuarioId, DescripcionCorta, Categoria, Gravedad, Lugar'
                })
            }

        # Validar gravedad
        gravedades_validas = ['debil', 'moderado', 'fuerte']
        if gravedad not in gravedades_validas:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Gravedad no válida. Debe ser uno de: {", ".join(gravedades_validas)}'
                })
            }

        # Validar categoría
        categorias_validas = [
            'Fugas',
            'Calidad del Inmobiliario',
            'Limpieza y desorden',
            'Calidad de los Servicios (Luz, Internet, Agua)',
            'Aulas Cerradas',
            'Objeto Perdido'
        ]
        if categoria not in categorias_validas:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Categoría no válida. Debe ser una de: {", ".join(categorias_validas)}'
                })
            }

        # Generar ID único para el incidente
        incidente_id = str(uuid.uuid4())

        # Fecha y hora actual en formato ISO
        fecha_actual = datetime.now().isoformat()

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        tabla_incidentes = dynamodb.Table(os.environ['TABLE_INCIDENTES'])

        # Crear registro del incidente
        incidente = {
            'id': incidente_id,
            'UsuarioId': usuario_id,
            'DescripcionCorta': descripcion_corta,
            'Categoria': categoria,
            'Gravedad': gravedad,
            'Lugar': lugar,
            'Estado': 'Notificado',  # Estado inicial siempre es "Notificado"
            'FechaCreacion': fecha_actual,
            'FechaActualizacion': fecha_actual
        }

        # Guardar en DynamoDB
        tabla_incidentes.put_item(Item=incidente)

        print(f"Incidente creado exitosamente con ID: {incidente_id}")

        # Retornar éxito
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Incidente creado exitosamente',
                'incidente': incidente
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