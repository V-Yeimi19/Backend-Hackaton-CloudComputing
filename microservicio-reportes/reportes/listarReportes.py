import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['INCIDENTES_TABLE'])

def lambda_handler(event, context):
    print(f"Evento recibido en listarReportes: {json.dumps(event)}")
    try:
        # Obtener parámetros de query (opcionales)
        query_params = event.get('queryStringParameters') or {}
        usuario_id = query_params.get('UsuarioId')
        estado = query_params.get('Estado')
        categoria = query_params.get('Categoria')
        
        estados_validos = ['Notificado', 'En Proceso', 'Finalizado']

        if estado and estado not in estados_validos:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}'})
            }

        # Escanear todos los reportes (en producción usar índices GSI)
        response = table.scan()
        reportes = response.get('Items', [])
        
        # Filtrar por parámetros si se proporcionan
        if usuario_id:
            reportes = [r for r in reportes if r.get('UsuarioId') == usuario_id]
        if estado:
            reportes = [r for r in reportes if r.get('Estado') == estado]
        if categoria:
            reportes = [r for r in reportes if r.get('Categoria') == categoria]
        
        # Ordenar por fecha de creación (más recientes primero)
        reportes.sort(key=lambda x: x.get('FechaCreacion', ''), reverse=True)
        print(f"Reportes listados exitosamente. Total: {len(reportes)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'reportes': reportes,
                'total': len(reportes)
            })
        }
        
    except Exception as e:
        print(f"Error en listarReportes: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
