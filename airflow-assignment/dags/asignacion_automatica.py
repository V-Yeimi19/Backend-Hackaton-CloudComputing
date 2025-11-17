"""
DAG de Airflow para asignación automática de incidentes a empleados.

Flujo:
1. Detecta nuevos incidentes sin asignar
2. Busca empleados disponibles de la categoría/área correspondiente
3. Asigna el incidente al primer empleado disponible
4. Si no hay disponibles, espera y reintenta
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.http.hooks.http import HttpHook
import json
import os
import boto3
from botocore.exceptions import ClientError

# Configuración
default_args = {
    'owner': 'alerta-utec',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Variables de entorno (configurar en Airflow)
INCIDENTES_TABLE = os.environ.get('INCIDENTES_TABLE', 'Incidentes')
USUARIOS_TABLE = os.environ.get('USUARIOS_TABLE', 'tabla_usuarios')
LAMBDA_API_URL = os.environ.get('LAMBDA_API_URL', 'https://your-api-id.execute-api.us-east-1.amazonaws.com')

dag = DAG(
    'asignacion_automatica_incidentes',
    default_args=default_args,
    description='Asigna automáticamente incidentes a empleados disponibles',
    schedule_interval=timedelta(minutes=2),  # Ejecutar cada 2 minutos
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['incidentes', 'asignacion'],
)


def obtener_incidentes_sin_asignar(**context):
    """
    Obtiene todos los incidentes sin asignar de DynamoDB.
    """
    # Configurar DynamoDB con credenciales de AWS Academy
    dynamodb = boto3.resource(
        'dynamodb', 
        region_name='us-east-1',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('AWS_SESSION_TOKEN')
    )
    incidentes_table = dynamodb.Table(INCIDENTES_TABLE)
    
    try:
        # Escanear incidentes sin asignar
        response = incidentes_table.scan(
            FilterExpression='attribute_not_exists(asignadoA)'
        )
        
        incidentes = response.get('Items', [])
        
        # Filtrar solo los que tienen estado "Reportado" o "Pendiente"
        incidentes_pendientes = [
            inc for inc in incidentes 
            if inc.get('estado') in ['Reportado', 'Pendiente']
        ]
        
        print(f"Encontrados {len(incidentes_pendientes)} incidentes sin asignar")
        
        # Guardar en XCom para el siguiente paso
        context['ti'].xcom_push(key='incidentes_sin_asignar', value=incidentes_pendientes)
        
        return incidentes_pendientes
        
    except ClientError as e:
        print(f"Error obteniendo incidentes: {e}")
        return []


def buscar_empleado_disponible(**context):
    """
    Para cada incidente sin asignar, busca un empleado disponible de la categoría correspondiente.
    """
    # Obtener incidentes del paso anterior
    ti = context['ti']
    incidentes = ti.xcom_pull(key='incidentes_sin_asignar', task_ids='obtener_incidentes_sin_asignar')
    
    if not incidentes:
        print("No hay incidentes sin asignar")
        return []
    
    # Configurar DynamoDB con credenciales de AWS Academy
    dynamodb = boto3.resource(
        'dynamodb', 
        region_name='us-east-1',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('AWS_SESSION_TOKEN')
    )
    usuarios_table = dynamodb.Table(USUARIOS_TABLE)
    
    asignaciones = []
    
    for incidente in incidentes:
        incidente_id = incidente.get('id')
        area_responsable = incidente.get('areaResponsable')
        
        if not area_responsable:
            print(f"Incidente {incidente_id} no tiene área responsable")
            continue
        
        try:
            # Buscar empleados de esa área
            response = usuarios_table.scan(
                FilterExpression='rol = :rol AND area = :area',
                ExpressionAttributeValues={
                    ':rol': 'trabajador',
                    ':area': area_responsable
                }
            )
            
            empleados = response.get('Items', [])
            
            if not empleados:
                print(f"No hay empleados disponibles para el área {area_responsable}")
                continue
            
            # Buscar empleado sin incidentes asignados pendientes
            empleado_disponible = None
            for empleado in empleados:
                empleado_email = empleado.get('email')
                
                # Verificar cuántos incidentes tiene asignados pendientes
                incidentes_table = dynamodb.Table(INCIDENTES_TABLE)
                response_inc = incidentes_table.scan(
                    FilterExpression='asignadoA = :email AND estado IN (:estado1, :estado2)',
                    ExpressionAttributeValues={
                        ':email': empleado_email,
                        ':estado1': 'En atencion',
                        ':estado2': 'Pendiente'
                    }
                )
                
                incidentes_asignados = response_inc.get('Items', [])
                
                # Si tiene menos de 3 incidentes pendientes, está disponible
                if len(incidentes_asignados) < 3:
                    empleado_disponible = empleado_email
                    break
            
            if empleado_disponible:
                asignaciones.append({
                    'incidenteId': incidente_id,
                    'empleadoEmail': empleado_disponible,
                    'area': area_responsable
                })
                print(f"Asignando incidente {incidente_id} a {empleado_disponible}")
            else:
                print(f"No hay empleados disponibles para el área {area_responsable}")
                
        except ClientError as e:
            print(f"Error buscando empleados: {e}")
            continue
    
    # Guardar asignaciones en XCom
    ti.xcom_push(key='asignaciones', value=asignaciones)
    
    return asignaciones


def asignar_incidentes(**context):
    """
    Llama al Lambda para asignar cada incidente a su empleado usando boto3.
    """
    import boto3
    
    ti = context['ti']
    asignaciones = ti.xcom_pull(key='asignaciones', task_ids='buscar_empleado_disponible')
    
    if not asignaciones:
        print("No hay asignaciones para realizar")
        return []
    
    # Configurar cliente Lambda con credenciales de AWS Academy (incluye session token)
    lambda_client = boto3.client(
        'lambda', 
        region_name='us-east-1',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('AWS_SESSION_TOKEN')
    )
    lambda_function_name = os.environ.get('LAMBDA_ASIGNAR_FUNCTION', 
                                          'alerta-utec-airflow-assignment-prod-asignarIncidenteEmpleado')
    
    resultados = []
    
    for asignacion in asignaciones:
        incidente_id = asignacion['incidenteId']
        empleado_email = asignacion['empleadoEmail']
        
        try:
            # Invocar Lambda directamente
            payload = {
                'pathParameters': {
                    'id': incidente_id
                },
                'body': json.dumps({
                    'empleadoEmail': empleado_email
                })
            }
            
            response = lambda_client.invoke(
                FunctionName=lambda_function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            response_payload = json.loads(response['Payload'].read())
            
            if response_payload.get('statusCode') == 200:
                print(f"✓ Incidente {incidente_id} asignado a {empleado_email}")
                resultados.append({'success': True, 'incidenteId': incidente_id})
            else:
                print(f"✗ Error asignando incidente {incidente_id}: {response_payload}")
                resultados.append({'success': False, 'incidenteId': incidente_id})
                
        except Exception as e:
            print(f"Error llamando Lambda para {incidente_id}: {e}")
            resultados.append({'success': False, 'incidenteId': incidente_id})
    
    ti.xcom_push(key='resultados_asignacion', value=resultados)
    
    return resultados


# Definir tareas
tarea_obtener_incidentes = PythonOperator(
    task_id='obtener_incidentes_sin_asignar',
    python_callable=obtener_incidentes_sin_asignar,
    dag=dag,
)

tarea_buscar_empleados = PythonOperator(
    task_id='buscar_empleado_disponible',
    python_callable=buscar_empleado_disponible,
    dag=dag,
)

tarea_asignar = PythonOperator(
    task_id='asignar_incidentes',
    python_callable=asignar_incidentes,
    dag=dag,
)

# Definir flujo
tarea_obtener_incidentes >> tarea_buscar_empleados >> tarea_asignar

