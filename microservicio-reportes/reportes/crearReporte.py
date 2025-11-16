import boto3
import json
import os
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['INCIDENTES_TABLE'])

def lambda_handler(event, context):
    print(f"Evento recibido en crearReporte: {json.dumps(event)}")
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validar campos requeridos
        required_fields = ['UsuarioId', 'DescripcionCorta', 'Categoria', 'Gravedad', 'Lugar']
        for field in required_fields:
            if field not in body:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Falta el campo requerido: {field}'})
                }
        
        # Validar categoría
        categorias_validas = [
            'Limpieza y desorden',
            'Fugas',
            'Calidad del inmobiliario',
            'Calidad de lo servicios (Luz, Internet, Agua)',
            'Aulas cerradas',
            'Objeto perdido'
        ]
        if body['Categoria'] not in categorias_validas:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Categoría inválida. Debe ser una de: {", ".join(categorias_validas)}'})
            }
        
        # Validar gravedad
        gravedades_validas = ['debil', 'moderado', 'fuerte']
        if body['Gravedad'] not in gravedades_validas:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Gravedad inválida. Debe ser una de: {", ".join(gravedades_validas)}'})
            }
        
        # Crear reporte
        reporte_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'id': reporte_id,
            'UsuarioId': body['UsuarioId'],
            'DescripcionCorta': body['DescripcionCorta'],
            'Categoria': body['Categoria'],
            'Gravedad': body['Gravedad'],
            'Lugar': body['Lugar'],
            'Estado': 'Notificado',  # Estado inicial
            'FechaCreacion': timestamp,
            'FechaActualizacion': timestamp
        }
        
        table.put_item(Item=item)
        print(f"Reporte creado exitosamente: {json.dumps(item)}")
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Reporte creado exitosamente',
                'reporte': item
            })
        }
        
    except Exception as e:
        print(f"Error en crearReporte: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
