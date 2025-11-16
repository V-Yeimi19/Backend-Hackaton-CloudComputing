import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table_asignaciones = dynamodb.Table(os.environ['ASIGNACIONES_TABLE'])

def lambda_handler(event, context):
    try:
        reporte_id = event['pathParameters']['id']
        
        response = table_asignaciones.get_item(Key={'ReporteId': reporte_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'No se encontraron responsables asignados para este reporte'})
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response['Item'])
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

