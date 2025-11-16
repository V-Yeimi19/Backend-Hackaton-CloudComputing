import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['REPORTES_TABLE'])

def lambda_handler(event, context):
    try:
        # Obtener todos los reportes
        response = table.scan()
        reportes = response.get('Items', [])
        
        # Filtrar solo reportes activos (no solucionados)
        reportes_activos = [
            r for r in reportes 
            if r.get('Estado') in ['Notificado', 'En Proceso']
        ]
        
        # Ordenar por fecha de creación (más recientes primero)
        reportes_activos.sort(key=lambda x: x.get('FechaCreacion', ''), reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'reportes_activos': reportes_activos,
                'total': len(reportes_activos)
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
