import boto3
import json
import os

# Cliente Lambda para invocar otras funciones
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    """
    Lambda para manejar eventos de WebSocket.

    Cuando se crea un incidente nuevo, este lambda recibe la notificación
    y automáticamente invoca Lambda_GestionTrabajadores para asignar un trabajador.
    """
    try:
        print("WebSocket event recibido:", json.dumps(event))

        # Determinar el tipo de conexión WebSocket
        route_key = event.get('requestContext', {}).get('routeKey')
        connection_id = event.get('requestContext', {}).get('connectionId')

        # Manejo de conexión
        if route_key == '$connect':
            return handle_connect(connection_id)

        # Manejo de desconexión
        elif route_key == '$disconnect':
            return handle_disconnect(connection_id)

        # Manejo de mensajes personalizados
        elif route_key == '$default' or route_key == 'nuevoIncidente':
            return handle_nuevo_incidente(event)

        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Ruta no reconocida: {route_key}'})
            }

    except Exception as e:
        print("Exception:", str(e))
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def handle_connect(connection_id):
    """
    Maneja nuevas conexiones WebSocket.
    Opcionalmente, puedes guardar el connection_id en DynamoDB para enviar mensajes después.
    """
    print(f"Nueva conexión WebSocket: {connection_id}")

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Conectado exitosamente'})
    }

def handle_disconnect(connection_id):
    """
    Maneja desconexiones WebSocket.
    Limpia el connection_id de DynamoDB si lo guardaste.
    """
    print(f"Desconexión WebSocket: {connection_id}")

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Desconectado exitosamente'})
    }

def handle_nuevo_incidente(event):
    """
    Maneja el evento de nuevo incidente.
    Invoca automáticamente Lambda_GestionTrabajadores para asignar un trabajador.
    """
    try:
        # Parse del body del mensaje WebSocket
        body = event.get('body')
        if isinstance(body, str):
            body = json.loads(body)

        # Obtener el ID del incidente
        incidente_id = body.get('incidenteId') or body.get('id')

        if not incidente_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Falta el campo incidenteId'
                })
            }

        print(f"Nuevo incidente detectado: {incidente_id}")
        print(f"Invocando Lambda_GestionTrabajadores para asignar trabajador...")

        # Invocar Lambda_GestionTrabajadores de forma asíncrona
        function_name = os.environ.get('LAMBDA_GESTION_TRABAJADORES', 'api-authentication-dev-gestionTrabajadores')

        payload = {
            'body': json.dumps({
                'id': incidente_id
            })
        }

        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # Asíncrono, no espera respuesta
            Payload=json.dumps(payload)
        )

        print(f"Lambda_GestionTrabajadores invocada. StatusCode: {response['StatusCode']}")

        # Retornar confirmación
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notificación recibida. Asignando trabajador automáticamente...',
                'incidenteId': incidente_id,
                'lambdaInvocada': function_name
            })
        }

    except Exception as e:
        print(f"Error al procesar nuevo incidente: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f'Error al procesar incidente: {str(e)}'
            })
        }
