import boto3
import os
import time

athena = boto3.client('athena')

def ejecutar_query(query: str):
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': os.environ['GLUE_DATABASE']},
        WorkGroup=os.environ['ATHENA_WORKGROUP']
    )
    return response['QueryExecutionId']

def esperar_resultados(query_execution_id):
    while True:
        status = athena.get_query_execution(QueryExecutionId=query_execution_id)['QueryExecution']['Status']['State']
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            return status
        time.sleep(1)

def obtener_resultados(query_execution_id):
    result = athena.get_query_results(QueryExecutionId=query_execution_id)
    headers = [col['Name'] for col in result['ResultSet']['ResultSetMetadata']['ColumnInfo']]
    rows = []
    for row in result['ResultSet']['Rows'][1:]:
        rows.append({headers[i]: col.get('VarCharValue', '') for i, col in enumerate(row['Data'])})
    return rows
