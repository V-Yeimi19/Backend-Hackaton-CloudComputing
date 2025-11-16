import boto3
import json
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['INCIDENTES_TABLE'])

def lambda_handler(event, context):
    print(f"Evento recibido en actualizarEstadoReporte: {json.dumps(event)}")
    try:
        reporte_id = event['pathParameters']['id']
        
        # 1. Obtener el reporte actual para verificar su estado
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
            
        item_actual = response['Item']
        estado_actual = item_actual.get('Estado')
        
        # 2. Determinar el nuevo estado basado en el estado actual
        nuevo_estado = ''
        if estado_actual == 'Notificado':
            nuevo_estado = 'En Proceso'
        elif estado_actual == 'En Proceso':
            nuevo_estado = 'Finalizado'
        elif estado_actual == 'Finalizado':
            # Si ya está finalizado, no hay nada que hacer
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'message': 'El reporte ya está finalizado, no se puede actualizar el estado.'})
            }
        else:
            # Manejar estados no esperados o iniciales
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'El estado actual "{estado_actual}" no permite una transición automática.'})
            }

        # 3. Actualizar el estado en DynamoDB
        update_expression = 'SET Estado = :estado, FechaActualizacion = :fecha'
        expression_attribute_values = {
            ':estado': nuevo_estado,
            ':fecha': datetime.utcnow().isoformat()
        }

        table.update_item(
            Key={'id': reporte_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        print(f"Estado del reporte {reporte_id} actualizado a: {nuevo_estado}")
        
        # 4. Obtener y devolver el reporte actualizado
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
        print(f"Error en actualizarEstadoReporte: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
