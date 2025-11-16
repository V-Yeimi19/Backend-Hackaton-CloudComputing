from utils.athena_utils import *
import json

def lambda_handler(event, context):
    query = """
    SELECT AVG(date_diff('hour', parse_datetime(FechaCreacion, '%Y-%m-%dT%H:%i:%s'), parse_datetime(FechaCierre, '%Y-%m-%dT%H:%i:%s'))) AS horas_promedio
    FROM reportes
    WHERE Estado = 'Solucionado';
    """
    qid = ejecutar_query(query)
    state = esperar_resultados(qid)
    if state != "SUCCEEDED":
        return {"statusCode": 500, "body": json.dumps({"error": "Query falló"})}
    data = obtener_resultados(qid)
    return {"statusCode": 200, "headers": {"Access-Control-Allow-Origin": "*"}, "body": json.dumps(data)}
