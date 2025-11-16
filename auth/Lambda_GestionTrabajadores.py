import boto3
from boto3.dynamodb.conditions import Attr
import json
import os
from datetime import datetime
import urllib.request
import urllib.error

def llamar_api_airflow(url, payload):
    """
    Realiza una llamada HTTP POST a la API de Airflow.
    """
    try:
        # Convertir payload a JSON
        data = json.dumps(payload).encode('utf-8')

        # Crear request
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        # Realizar llamada
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read().decode('utf-8')
            return json.loads(response_data)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Error HTTP {e.code}: {error_body}")
        try:
            return json.loads(error_body)
        except:
            return {'error': f'HTTP {e.code}: {error_body}'}

    except Exception as e:
        print(f"Error llamando a Airflow: {str(e)}")
        return {'error': str(e)}

# Mapeo de categorías a roles de trabajadores
CATEGORIA_A_ROL = {
    'Fugas': 'Tecnico de Mantenimiento',
    'Calidad del Inmobiliario': 'Tecnico de Mantenimiento',
    'Limpieza y desorden': 'Personal de Limpieza',
    'Calidad de los Servicios (Luz, Internet, Agua)': 'OIT',
    'Aulas Cerradas': 'Seguridad',
    'Objeto Perdido': 'Seguridad'
}

def obtener_rol_por_categoria(categoria):
    """Obtiene el rol del trabajador según la categoría del incidente"""
    return CATEGORIA_A_ROL.get(categoria)

def obtener_trabajador_disponible(tabla_usuarios, rol_requerido):
    """
    Busca un trabajador cuyo area_trabajo coincida con el rol requerido
    y cuyo role sea 'Trabajador'.
    """
    try:
        response = tabla_usuarios.scan(
            FilterExpression=Attr("role").eq("Trabajador") & Attr("area_trabajo").eq(rol_requerido)
        )

        trabajadores = response.get('Items', [])

        if not trabajadores:
            return None

        return trabajadores[0]

    except Exception as e:
        print(f"Error al buscar trabajador: {str(e)}")
        return None

def lambda_handler(event, context):
    """
    Lambda para asignar un incidente existente a un trabajador según la categoría.
    El incidente debe existir previamente con estado 'Notificado'.
    """
    try:
        # Debug: imprimir el evento completo
        print("Event recibido:", json.dumps(event))

        # Parse del body si viene como string JSON
        if 'body' in event and event['body']:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event

        print("Body parseado:", body)

        # Obtener el ID del incidente
        incidente_id = body.get('id')

        # Validar campo obligatorio
        if not incidente_id:
            return {
                'statusCode': 400,
                'body':  {
                    'error': 'Falta el campo requerido: id'
                }
            }

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        tabla_usuarios = dynamodb.Table(os.environ['TABLE_USUARIOS'])
        tabla_incidentes = dynamodb.Table(os.environ['TABLE_INCIDENTES'])

        # Obtener el incidente existente
        response = tabla_incidentes.get_item(Key={'id': incidente_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': {
                    'error': 'Incidente no encontrado'
                }
            }

        incidente = response['Item']

        # Validar que el incidente esté en estado 'Notificado'
        if incidente.get('Estado') != 'Notificado':
            return {
                'statusCode': 400,
                'body': {
                    'error': f'El incidente debe estar en estado "Notificado". Estado actual: {incidente.get("Estado")}'
                }
            }

        # Obtener la categoría del incidente
        categoria = incidente.get('Categoria')

        # Validar categoría y obtener rol requerido
        rol_requerido = obtener_rol_por_categoria(categoria)
        if not rol_requerido:
            return {
                'statusCode': 400,
                'body':{
                    'error': f'Categoría no válida: {categoria}. Categorías permitidas: {", ".join(CATEGORIA_A_ROL.keys())}'
                }
            }

        # Buscar trabajador disponible
        trabajador = obtener_trabajador_disponible(tabla_usuarios, rol_requerido)

        if not trabajador:
            return {
                'statusCode': 404,
                'body': {
                    'error': f'No se encontró ningún trabajador disponible con rol: {rol_requerido}'
                }
            }

        # PASO 1: Validar cambio de estado con Airflow (Notificado -> En Proceso)
        airflow_base_url = os.environ['AIRFLOW_API_URL']
        validacion_payload = {
            'incidenteId': incidente_id,
            'estadoActual': 'Notificado',
            'estadoNuevo': 'En Proceso'
        }

        print(f"Validando asignación con Airflow: Notificado → En Proceso")
        validacion_response = llamar_api_airflow(
            f"{airflow_base_url}/airflow/validar-cambio-estado",
            validacion_payload
        )

        # Verificar si hay error en la validación
        if 'error' in validacion_response:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f'Error al validar con Airflow: {validacion_response["error"]}'
                })
            }

        # Verificar si el cambio es válido
        validacion_body = validacion_response.get('body', {})
        if isinstance(validacion_body, str):
            validacion_body = json.loads(validacion_body)

        if not validacion_body.get('valido', False):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': validacion_body.get('error', 'Cambio de estado no válido'),
                    'estadosPermitidos': validacion_body.get('estadosPermitidos', [])
                })
            }

        print(f"Validación exitosa. WorkflowId: {validacion_body.get('workflowId')}")

        # PASO 2: Ejecutar workflow en Airflow
        workflow_payload = {
            'incidenteId': incidente_id,
            'estadoNuevo': 'En Proceso',
            'trabajadorId': trabajador['correo']
        }

        print(f"Ejecutando workflow de asignación en Airflow")
        workflow_response = llamar_api_airflow(
            f"{airflow_base_url}/airflow/ejecutar-workflow",
            workflow_payload
        )

        # Verificar si hay error en el workflow
        if 'error' in workflow_response:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': f'Error al ejecutar workflow: {workflow_response["error"]}'
                })
            }

        workflow_body = workflow_response.get('body', {})
        if isinstance(workflow_body, str):
            workflow_body = json.loads(workflow_body)

        if not workflow_body.get('success', False):
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'El workflow de Airflow falló',
                    'detalles': workflow_body
                })
            }

        print(f"Workflow ejecutado exitosamente. Tareas: {len(workflow_body.get('tareasEjecutadas', []))}")

        # PASO 3: Actualizar DynamoDB después de validación exitosa de Airflow
        fecha_actualizacion = datetime.now().isoformat()

        tabla_incidentes.update_item(
            Key={'id': incidente_id},
            UpdateExpression='SET TrabajadorId = :trabajador_id, Estado = :estado, FechaActualizacion = :fecha',
            ExpressionAttributeValues={
                ':trabajador_id': trabajador['correo'],
                ':estado': 'En Proceso',
                ':fecha': fecha_actualizacion
            }
        )

        # Retornar éxito con información del workflow de Airflow
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Incidente asignado exitosamente',
                'incidenteId': incidente_id,
                'trabajadorAsignado': {
                    'id': trabajador['correo'],
                    'nombre': trabajador.get('nombre', 'N/A'),
                    'rol': trabajador['rol']
                },
                'estadoAnterior': 'Notificado',
                'estadoActual': 'En Proceso',
                'fechaAsignacion': fecha_actualizacion,
                'airflowWorkflow': {
                    'workflowId': workflow_body.get('workflowId'),
                    'tareasEjecutadas': len(workflow_body.get('tareasEjecutadas', [])),
                    'tiempoEjecucion': workflow_body.get('tiempoEjecucion')
                }
            })
        }

    except Exception as e:
        print("Exception:", str(e))
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
