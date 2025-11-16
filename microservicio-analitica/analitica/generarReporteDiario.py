import json
import boto3
import datetime
from utils.athena_utils import *

s3 = boto3.client('s3')
bucket = os.environ['S3_BUCKET_ANALYTICS']

def lambda_handler(event, context):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d")
    consultas = {
        "por_categoria": "SELECT Categoria, COUNT(*) AS total FROM reportes GROUP BY Categoria ORDER BY total DESC;",
        "por_estado": "SELECT Estado, COUNT(*) AS total FROM reportes GROUP BY Estado ORDER BY total DESC;"
    }
    resultado_final = {}
    for nombre, sql in consultas.items():
        qid = ejecutar_query(sql)
        esperar_resultados(qid)
        resultado_final[nombre] = obtener_resultados(qid)
    key = f"estadisticas/{fecha}/summary.json"
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(resultado_final), ContentType="application/json")
    return {"statusCode": 200, "body": json.dumps({"archivo": key})}
