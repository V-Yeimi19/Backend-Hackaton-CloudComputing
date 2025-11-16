import boto3
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

def lambda_handler(event, context):
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
            # Si no hay body, asumir que el event es el body directamente
            body = event

        # Debug: imprimir el body parseado
        print("Body parseado:", body)

        # Obtener los campos requeridos
        incidente_id = body.get('id')
        nuevo_status = body.get('status')
        resolved_by = body.get('resolvedBy') 

        # Validar campos obligatorios
        if not all([incidente_id, nuevo_status]):
            return {
                'statusCode': 400,
                'body': {
                    'error': 'Faltan campos requeridos: id, status'
                }
            }

        # Validar estados permitidos
        estados_validos = ['Notificado', 'En Proceso', 'Finalizado']
        if nuevo_status not in estados_validos:
            return {
                'statusCode': 400,
                'body': {
                    'error': f'Estado no válido. Debe ser uno de: {", ".join(estados_validos)}'
                }
            }

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        tabla_incidentes = dynamodb.Table(os.environ['TABLE_INCIDENTES'])

        # Obtener el incidente actual
        response = tabla_incidentes.get_item(Key={'id': incidente_id})

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': {
                    'error': 'Incidente no encontrado'
                }
            }

        incidente_actual = response['Item']
        estado_actual = incidente_actual.get('Estado', 'Notificado')

        # PASO 1: Validar cambio de estado con Airflow
        airflow_base_url = os.environ['AIRFLOW_API_URL']
        validacion_payload = {
            'incidenteId': incidente_id,
            'estadoActual': estado_actual,
            'estadoNuevo': nuevo_status
        }

        print(f"Validando cambio de estado con Airflow: {estado_actual} → {nuevo_status}")
        validacion_response = llamar_api_airflow(
            f"{airflow_base_url}/airflow/validar-cambio-estado",
            validacion_payload
        )

        # Verificar si hay error en la respuesta de validación
        if 'error' in validacion_response:
            return {
                'statusCode': 500,
                'body': {
                    'error': f'Error al validar con Airflow: {validacion_response["error"]}'
                }
            }

        # Verificar si el cambio es válido
        validacion_body = validacion_response.get('body', {})
        if isinstance(validacion_body, str):
            validacion_body = json.loads(validacion_body)

        if not validacion_body.get('valido', False):
            return {
                'statusCode': 400,
                'body': {
                    'error': validacion_body.get('error', 'Cambio de estado no válido'),
                    'estadosPermitidos': validacion_body.get('estadosPermitidos', [])
                }
            }

        print(f"Validación exitosa. WorkflowId: {validacion_body.get('workflowId')}")

        # PASO 2: Ejecutar workflow en Airflow
        workflow_payload = {
            'incidenteId': incidente_id,
            'estadoNuevo': nuevo_status,
            'trabajadorId': incidente_actual.get('TrabajadorId', 'N/A')
        }

        print(f"Ejecutando workflow en Airflow para incidente {incidente_id}")
        workflow_response = llamar_api_airflow(
            f"{airflow_base_url}/airflow/ejecutar-workflow",
            workflow_payload
        )

        # Verificar si hay error en el workflow
        if 'error' in workflow_response:
            return {
                'statusCode': 500,
                'body': {
                    'error': f'Error al ejecutar workflow: {workflow_response["error"]}'
                }
            }

        workflow_body = workflow_response.get('body', {})
        if isinstance(workflow_body, str):
            workflow_body = json.loads(workflow_body)

        if not workflow_body.get('success', False):
            return {
                'statusCode': 500,
                'body': {
                    'error': 'El workflow de Airflow falló',
                    'detalles': workflow_body
                }
            }

        print(f"Workflow ejecutado exitosamente. Tareas: {len(workflow_body.get('tareasEjecutadas', []))}")

        # PASO 3: Actualizar DynamoDB basándose en la respuesta exitosa de Airflow
        updated_at = datetime.now().isoformat()

        # Preparar la expresión de actualización
        update_expression = 'SET Estado = :status, FechaActualizacion = :updated_at'
        expression_attribute_values = {
            ':status': nuevo_status,
            ':updated_at': updated_at
        }

        # Si el estado es "Finalizado", agregar campos adicionales
        if nuevo_status == 'Finalizado':
            update_expression += ', FechaResolucion = :resolved_at'
            expression_attribute_values[':resolved_at'] = updated_at

            if resolved_by:
                update_expression += ', ResueltoPor = :resolved_by'
                expression_attribute_values[':resolved_by'] = resolved_by

        # Actualizar el incidente en DynamoDB
        tabla_incidentes.update_item(
            Key={'id': incidente_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values
        )

        # Retornar éxito con información del workflow de Airflow
        response_body = {
            'message': 'Incidente actualizado exitosamente',
            'id': incidente_id,
            'estadoAnterior': estado_actual,
            'estadoActual': nuevo_status,
            'updatedAt': updated_at,
            'airflowWorkflow': {
                'workflowId': workflow_body.get('workflowId'),
                'tareasEjecutadas': len(workflow_body.get('tareasEjecutadas', [])),
                'tiempoEjecucion': workflow_body.get('tiempoEjecucion')
            }
        }

        if nuevo_status == 'Finalizado':
            response_body['resolvedAt'] = updated_at
            if resolved_by:
                response_body['resolvedBy'] = resolved_by

        return {
            'statusCode': 200,
            'body': response_body
        }

    except Exception as e:
        # Excepción y retornar un código de error HTTP 500
        print("Exception:", str(e))
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
