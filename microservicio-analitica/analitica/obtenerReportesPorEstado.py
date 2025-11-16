from utils.athena_utils import *
import json

def lambda_handler(event, context):
    query = "SELECT Estado, COUNT(*) AS total FROM reportes GROUP BY Estado ORDER BY total DESC;"
    qid = ejecutar_query(query)
    state = esperar_resultados(qid)
    if state != "SUCCEEDED":
        return {"statusCode": 500, "body": json.dumps({"error": "Query falló"})}
    data = obtener_resultados(qid)
    return {"statusCode": 200, "headers": {"Access-Control-Allow-Origin": "*"}, "body": json.dumps(data)}
