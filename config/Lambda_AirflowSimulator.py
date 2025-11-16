import json
from datetime import datetime

def lambda_handler(event, context):
    """
    Simulador de API Airflow para procesar cambios de estado de incidentes.

    Endpoints simulados:
    - POST /airflow/validar-cambio-estado
    - POST /airflow/ejecutar-workflow
    """
    try:
        print("Event recibido:", json.dumps(event))

        # Parse del body
        if 'body' in event and event['body']:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        else:
            body = event

        # Determinar el endpoint basado en el path
        path = event.get('path', '')

        if 'validar-cambio-estado' in path:
            return validar_cambio_estado(body)
        elif 'ejecutar-workflow' in path:
            return ejecutar_workflow(body)
        else:
            return {
                'statusCode': 404,
                'body': {
                    'error': 'Endpoint no encontrado'
                }
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

def validar_cambio_estado(body):
    """
    Valida si un cambio de estado es permitido según las reglas de negocio.
    """
    incidente_id = body.get('incidenteId')
    estado_actual = body.get('estadoActual')
    estado_nuevo = body.get('estadoNuevo')

    if not all([incidente_id, estado_actual, estado_nuevo]):
        return {
            'statusCode': 400,
            'body': {
                'valido': False,
                'error': 'Faltan campos requeridos: incidenteId, estadoActual, estadoNuevo'
            }
        }

    # Reglas de transición de estados
    transiciones_validas = {
        'Notificado': ['En Proceso'],
        'En Proceso': ['Finalizado'],
        'Finalizado': []  # No se puede cambiar de Finalizado
    }

    estados_permitidos = transiciones_validas.get(estado_actual, [])

    if estado_nuevo not in estados_permitidos:
        return {
            'statusCode': 200,
            'body': {
                'valido': False,
                'error': f'Transición no permitida: {estado_actual} → {estado_nuevo}',
                'estadosPermitidos': estados_permitidos
            }
        }

    # Validación exitosa - la transición es válida
    return {
        'statusCode': 200,
        'body': {
            'valido': True,
            'message': f'Cambio de estado válido: {estado_actual} → {estado_nuevo}',
            'workflowId': f'wf_{incidente_id}_{int(datetime.now().timestamp())}'
        }
    }

def ejecutar_workflow(body):
    """
    Simula la ejecución de un workflow en Airflow.

    Simula tareas como:
    - Enviar notificaciones
    - Registrar en logs
    - Validar permisos
    - Ejecutar acciones automatizadas
    """
def ejecutar_workflow(body):
    incidente_id = body.get('incidenteId')
    estado_nuevo = body.get('estadoNuevo')
    trabajador_id = body.get('trabajadorId')

    if not incidente_id or not estado_nuevo:
        return {
            'statusCode': 400,
            'body': {
                'success': False,
                'error': 'Faltan campos requeridos: incidenteId, estadoNuevo'
            }
        }

    # Simular tiempo de procesamiento del workflow
    workflow_id = f'dag_run_{incidente_id}_{int(datetime.now().timestamp())}'

    # Simular tareas del workflow según el estado
    tareas_ejecutadas = []

    if estado_nuevo == 'En Proceso':
        tareas_ejecutadas = [
            {
                'tarea': 'notificar_trabajador',
                'status': 'success',
                'mensaje': f'Notificación enviada al trabajador {trabajador_id}'
            },
            {
                'tarea': 'registrar_inicio',
                'status': 'success',
                'mensaje': 'Inicio de trabajo registrado'
            },
            {
                'tarea': 'actualizar_metricas',
                'status': 'success',
                'mensaje': 'Métricas de incidente actualizadas'
            }
        ]

    elif estado_nuevo == 'Finalizado':
        tareas_ejecutadas = [
            {
                'tarea': 'notificar_usuario',
                'status': 'success',
                'mensaje': 'Usuario notificado de la resolución'
            },
            {
                'tarea': 'cerrar_incidente',
                'status': 'success',
                'mensaje': 'Incidente marcado como cerrado'
            },
            {
                'tarea': 'generar_reporte',
                'status': 'success',
                'mensaje': 'Reporte de cierre generado'
            },
            {
                'tarea': 'actualizar_estadisticas',
                'status': 'success',
                'mensaje': 'Estadísticas de área actualizadas'
            }
        ]

    # Workflow siempre se ejecuta exitosamente
    return {
        'statusCode': 200,
        'body': {
            'success': True,
            'workflowId': workflow_id,
            'message': 'Workflow ejecutado exitosamente',
            'tareasEjecutadas': tareas_ejecutadas,
            'tiempoEjecucion': '2 segundos',
            'timestamp': datetime.now().isoformat()
        }
    }
