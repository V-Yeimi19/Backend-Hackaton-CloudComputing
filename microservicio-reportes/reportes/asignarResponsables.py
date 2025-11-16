import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table_reportes = dynamodb.Table(os.environ['INCIDENTES_TABLE'])
table_asignaciones = dynamodb.Table(os.environ['ASIGNACIONES_TABLE'])

def lambda_handler(event, context):
    try:
        reporte_id = event['pathParameters']['id']
        body = json.loads(event.get('body', '{}'))
        
        if 'TrabajadoresId' not in body:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'El campo TrabajadoresId es requerido (debe ser una lista)'})
            }
        
        trabajadores_id = body['TrabajadoresId']
        
        if not isinstance(trabajadores_id, list):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'TrabajadoresId debe ser una lista'})
            }
        
        # Verificar que el reporte existe
        response = table_reportes.get_item(Key={'id': reporte_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Reporte no encontrado'})
            }
        
        # Crear o actualizar asignación
        item = {
            'ReporteId': reporte_id,
            'TrabajadoresId': trabajadores_id
        }
        
        table_asignaciones.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Responsables asignados exitosamente',
                'asignacion': item
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

