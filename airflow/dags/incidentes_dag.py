from datetime import datetime, timedelta
import os
import json
import requests
import boto3

from airflow import DAG
from airflow.operators.python import PythonOperator

# Estas URLs las puedes poner como Variables de Airflow o como env vars luego.
API_BASE = os.environ.get("INCIDENTES_API_BASE")  # p.ej. https://<id>.execute-api.us-east-1.amazonaws.com
ADMIN_API_BASE = os.environ.get("ADMIN_API_BASE")  # p.ej. https://<id>.execute-api.us-east-1.amazonaws.com

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
INCIDENTES_TABLE_NAME = os.environ.get("INCIDENTES_TABLE_NAME", "Incidentes")


def fetch_open_incidents(**context):
    """
    Llama a tu endpoint de admin para traer incidentes activos (no cerrados).
    GET /admin/incidentes
    """
    url = f"{ADMIN_API_BASE}/admin/incidentes"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    # Guardamos en XCom para las siguientes tareas
    return data.get("items", [])


def auto_classify(incidentes, **context):
    """
    Clasificación muy simple basada en la descripción.
    Marca nivelDeGravedad sugerido.
    """
    clasificados = []
    for inc in incidentes:
        desc = (inc.get("descripcion") or "").lower()
        nivel = inc.get("nivelDeGravedad") or "Media"

        if any(p in desc for p in ["sangre", "herido", "pelea", "arma", "robo"]):
            nivel = "Alta"
        elif any(p in desc for p in ["fuga de agua", "fuego", "incendio"]):
            nivel = "Alta"
        elif any(p in desc for p in ["ruido", "molestia", "basura"]):
            nivel = "Baja"

        inc["nivelDeGravedad_sugerido"] = nivel
        clasificados.append(inc)

    return clasificados


def update_incidents_in_api(incidentes, **context):
    """
    Llama a tu endpoint de actualizar estado/nivel para aplicar la clasificación.
    PUT /incidentes/{id}/estado
    Solo actualizamos si el nivel sugerido es diferente.
    """
    for inc in incidentes:
        incidente_id = inc.get("id")
        actual = inc.get("nivelDeGravedad")
        sugerido = inc.get("nivelDeGravedad_sugerido")

        if not incidente_id or not sugerido:
            continue

        if actual == sugerido:
            continue  # nada que cambiar

        url = f"{API_BASE}/incidentes/{incidente_id}/estado"
        body = {
            "estado": inc.get("estado", "Reportado"),
            "nivelDeGravedad": sugerido,
            "descripcion": inc.get("descripcion", ""),
            "categoria": inc.get("categoria", ""),
        }
        print(f"Actualizando incidente {incidente_id} -> {sugerido}")
        resp = requests.put(url, json=body, timeout=10)
        if resp.status_code >= 300:
            print(f"Error actualizando incidente {incidente_id}: {resp.status_code} {resp.text}")


def send_high_severity_notifications(incidentes, **context):
    """
    Ejemplo: para incidentes con nivel Alta, podrías mandar correo o SMS.
    Aquí solo esqueleto: en la práctica llamarías SES/SNS o una Lambda tuya.
    """
    altos = [i for i in incidentes if i.get("nivelDeGravedad_sugerido") == "Alta"]
    if not altos:
        print("No hay incidentes de alta gravedad para notificar.")
        return

    print(f"Incidentes alta gravedad para notificar: {len(altos)}")
    for inc in altos:
        print(f"Notificar área {inc.get('areaResponsable')} por incidente {inc.get('id')}")
        # Aquí podrías:
        # - Llamar a una API tuya /notificar
        # - Usar boto3.client('sns') para enviar SMS/correo
        # De momento, solo dejamos el print para el hackathon.


default_args = {
    "owner": "alerta-utec",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="incidentes_clasificacion_y_notificaciones",
    default_args=default_args,
    description="Clasifica incidentes y envía notificaciones según gravedad",
    schedule_interval="*/10 * * * *",  # cada 10 minutos (ajusta según quieras)
    start_date=datetime(2025, 11, 16),
    catchup=False,
    tags=["incidentes", "alerta-utec"],
) as dag:

    tarea_fetch = PythonOperator(
        task_id="fetch_open_incidents",
        python_callable=fetch_open_incidents,
    )

    tarea_clasificar = PythonOperator(
        task_id="auto_classify_incidents",
        python_callable=auto_classify,
        op_kwargs={"incidentes": "{{ ti.xcom_pull(task_ids='fetch_open_incidents') }}"},
    )

    tarea_actualizar = PythonOperator(
        task_id="update_incidents_in_api",
        python_callable=update_incidents_in_api,
        op_kwargs={"incidentes": "{{ ti.xcom_pull(task_ids='auto_classify_incidents') }}"},
    )

    tarea_notificar = PythonOperator(
        task_id="send_high_severity_notifications",
        python_callable=send_high_severity_notifications,
        op_kwargs={"incidentes": "{{ ti.xcom_pull(task_ids='auto_classify_incidents') }}"},
    )

    tarea_fetch >> tarea_clasificar >> [tarea_actualizar, tarea_notificar]
