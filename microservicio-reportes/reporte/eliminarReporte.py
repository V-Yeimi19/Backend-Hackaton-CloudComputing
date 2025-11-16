import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table_reportes = dynamodb.Table(os.environ['REPORTES_TABLE'])
table_asignaciones = dynamodb.Table(os.environ['ASIGNACIONES_TABLE'])

def lambda_handler(event, context):
    try:
        reporte_id = event['pathParameters']['id']
        
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
        
        # Eliminar asignaciones relacionadas si existen
        try:
            asignacion_response = table_asignaciones.get_item(Key={'ReporteId': reporte_id})
            if 'Item' in asignacion_response:
                table_asignaciones.delete_item(Key={'ReporteId': reporte_id})
        except Exception:
            pass  # Si no hay asignaciones, continuar
        
        # Eliminar reporte
        table_reportes.delete_item(Key={'id': reporte_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'message': 'Reporte eliminado exitosamente'})
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

