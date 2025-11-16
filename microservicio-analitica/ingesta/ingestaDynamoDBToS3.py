import boto3
import json
import os
from datetime import datetime

s3 = boto3.client('s3')
glue = boto3.client('glue')

def lambda_handler(event, context):
    """
    Función Lambda que se activa con DynamoDB Streams.
    Extrae los cambios de la tabla Reporte y los guarda en S3 para análisis posterior.
    """
    try:
        bucket_name = os.environ['S3_BUCKET_ANALYTICS']
        
        # Procesar cada registro del stream
        for record in event['Records']:
            if record['eventName'] in ['INSERT', 'MODIFY']:
                # Obtener la nueva imagen del registro
                new_image = record.get('dynamodb', {}).get('NewImage', {})
                
                # Convertir DynamoDB format a JSON normal
                reporte_data = {}
                for key, value in new_image.items():
                    if 'S' in value:
                        reporte_data[key] = value['S']
                    elif 'N' in value:
                        reporte_data[key] = value['N']
                    elif 'L' in value:
                        reporte_data[key] = [item.get('S', item.get('N', '')) for item in value['L']]
                    elif 'BOOL' in value:
                        reporte_data[key] = value['BOOL']
                    elif 'NULL' in value:
                        reporte_data[key] = None
                
                # Generar clave S3 con timestamp para particionado
                timestamp = datetime.utcnow()
                year = timestamp.strftime('%Y')
                month = timestamp.strftime('%m')
                day = timestamp.strftime('%d')
                hour = timestamp.strftime('%H')
                
                # Clave S3: reportes/year=YYYY/month=MM/day=DD/hour=HH/timestamp-uuid.json
                s3_key = f"reportes/year={year}/month={month}/day={day}/hour={hour}/{timestamp.isoformat()}-{reporte_data.get('id', 'unknown')}.json"
                
                # Guardar en S3
                s3.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=json.dumps(reporte_data),
                    ContentType='application/json'
                )
                
                print(f"Registro guardado en S3: {s3_key}")
        
        # Después de procesar los registros, iniciar el crawler de Glue si hay cambios significativos
        # (Opcional: puedes hacerlo de forma periódica con EventBridge en lugar de aquí)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Procesados {len(event["Records"])} registros exitosamente'
            })
        }
        
    except Exception as e:
        print(f"Error en ingesta: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

