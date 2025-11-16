import boto3
import json
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['REPORTES_TABLE'])

def lambda_handler(event, context):
    try:
        query_params = event.get('queryStringParameters') or {}
        
        # Obtener todos los reportes
        response = table.scan()
        reportes = response.get('Items', [])
        
        # Aplicar filtros
        estados_validos = ['Notificado', 'En Proceso', 'Finalizado']

        if query_params.get('Estado'):
            estado = query_params['Estado']
            if estado not in estados_validos:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}'})
                }
            reportes = [r for r in reportes if r.get('Estado') == estado]
        
        if query_params.get('Categoria'):
            categoria = query_params['Categoria']
            reportes = [r for r in reportes if r.get('Categoria') == categoria]
        
        if query_params.get('Gravedad'):
            gravedad = query_params['Gravedad']
            reportes = [r for r in reportes if r.get('Gravedad') == gravedad]
        
        if query_params.get('Lugar'):
            lugar = query_params['Lugar']
            reportes = [r for r in reportes if lugar.lower() in r.get('Lugar', '').lower()]
        
        # Ordenar por fecha de creación (más recientes primero)
        reportes.sort(key=lambda x: x.get('FechaCreacion', ''), reverse=True)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'reportes': reportes,
                'total': len(reportes),
                'filtros_aplicados': query_params
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
