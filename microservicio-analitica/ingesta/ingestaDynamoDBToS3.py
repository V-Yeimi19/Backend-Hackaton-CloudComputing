import boto3
import json
import os
from datetime import datetime

s3 = boto3.client('s3')
glue = boto3.client('glue')

def lambda_handler(event, context):
    try:
        bucket_name = os.environ['S3_BUCKET_ANALYTICS']
        stage = os.environ['STAGE']  # NUEVO
        total = 0
        
        for record in event['Records']:
            if record['eventName'] in ['INSERT', 'MODIFY']:
                new_image = record.get('dynamodb', {}).get('NewImage', {})
                
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

                timestamp = datetime.utcnow()
                year = timestamp.strftime('%Y')
                month = timestamp.strftime('%m')
                day = timestamp.strftime('%d')
                hour = timestamp.strftime('%H')

                s3_key = f"reportes/year={year}/month={month}/day={day}/hour={hour}/{timestamp.isoformat()}-{reporte_data.get('id', 'unknown')}.json"

                s3.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=json.dumps(reporte_data),
                    ContentType='application/json'
                )

                print("Guardado en S3:", s3_key)
                total += 1

        # ============================
        #   INICIAR EL CRAWLER AQUÍ
        # ============================
        crawler_name = f"alerta-utec-analitica-crawler-{stage}"

        glue.start_crawler(Name=crawler_name)
        print("Crawler iniciado:", crawler_name)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Registros procesados: {total}. Crawler ejecutado.'
            })
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
