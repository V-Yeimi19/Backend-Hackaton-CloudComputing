import boto3
import json
import os
import time

athena = boto3.client('athena')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        query = body.get('query')
        
        if not query:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'El campo query es requerido'})
            }
        
        database = os.environ['GLUE_DATABASE']
        workgroup = os.environ['ATHENA_WORKGROUP']
        output_location = f"s3://{os.environ['S3_BUCKET_ANALYTICS']}/athena-results/"
        
        # Ejecutar consulta en Athena
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': output_location},
            WorkGroup=workgroup
        )
        
        query_execution_id = response['QueryExecutionId']
        
        # Esperar a que la consulta termine (máximo 30 segundos)
        max_wait_time = 30
        wait_interval = 1
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            status_response = athena.get_query_execution(QueryExecutionId=query_execution_id)
            status = status_response['QueryExecution']['Status']['State']
            
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            
            time.sleep(wait_interval)
            elapsed_time += wait_interval
        
        # Obtener resultados si la consulta fue exitosa
        if status == 'SUCCEEDED':
            results_response = athena.get_query_results(QueryExecutionId=query_execution_id)
            
            # Procesar resultados
            columns = [col['Name'] for col in results_response['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            rows = []
            
            for row in results_response['ResultSet']['Rows'][1:]:  # Saltar la primera fila (headers)
                row_data = {}
                for i, col in enumerate(columns):
                    row_data[col] = row['Data'][i].get('VarCharValue', '')
                rows.append(row_data)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'query_execution_id': query_execution_id,
                    'status': status,
                    'columns': columns,
                    'rows': rows,
                    'total_rows': len(rows)
                })
            }
        else:
            status_reason = status_response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': f'La consulta falló: {status}',
                    'reason': status_reason,
                    'query_execution_id': query_execution_id
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

