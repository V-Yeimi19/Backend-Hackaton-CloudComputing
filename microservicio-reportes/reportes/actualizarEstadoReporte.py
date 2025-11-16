import boto3
import json
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['REPORTES_TABLE'])

def lambda_handler(event, context):
    try:
        reporte_id = event['pathParameters']['id']
        body = json.loads(event.get('body', '{}'))
        
        if 'Estado' not in body:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'El campo Estado es requerido'})
            }
        
        nuevo_estado = body['Estado']
        estados_validos = ['PENDIENTE', 'EN ARREGLO', 'SOLUCIONADO']
        
        if nuevo_estado not in estados_validos:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}'})
            }
        
        # Verificar que el reporte existe
        response = table.get_item(Key={'id': reporte_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Reporte no encontrado'})
            }
        
        # Actualizar estado
        table.update_item(
            Key={'id': reporte_id},
            UpdateExpression='SET Estado = :estado, FechaActualizacion = :fecha',
            ExpressionAttributeValues={
                ':estado': nuevo_estado,
                ':fecha': datetime.utcnow().isoformat()
            },
            ReturnValues='ALL_NEW'
        )
        
        # Obtener el reporte actualizado
        updated_response = table.get_item(Key={'id': reporte_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Estado del reporte actualizado exitosamente',
                'reporte': updated_response['Item']
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

