import boto3
import json
import os
from collections import Counter

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['REPORTES_TABLE'])

def lambda_handler(event, context):
    try:
        # Obtener todos los reportes
        response = table.scan()
        reportes = response.get('Items', [])
        
        total_reportes = len(reportes)
        
        # Estadísticas por estado
        estados = [r.get('Estado', 'DESCONOCIDO') for r in reportes]
        estadisticas_estado = dict(Counter(estados))
        
        # Estadísticas por categoría
        categorias = [r.get('Categoria', 'DESCONOCIDA') for r in reportes]
        estadisticas_categoria = dict(Counter(categorias))
        categoria_mas_reportes = max(estadisticas_categoria.items(), key=lambda x: x[1]) if estadisticas_categoria else None
        
        # Estadísticas por gravedad
        gravedades = [r.get('Gravedad', 'DESCONOCIDA') for r in reportes]
        estadisticas_gravedad = dict(Counter(gravedades))
        
        # Reportes solucionados vs no solucionados
        solucionados = len([r for r in reportes if r.get('Estado') == 'SOLUCIONADO'])
        no_solucionados = total_reportes - solucionados
        
        # Reportes activos (pendientes + en arreglo)
        activos = len([r for r in reportes if r.get('Estado') in ['PENDIENTE', 'EN ARREGLO']])
        
        estadisticas = {
            'total_reportes': total_reportes,
            'por_estado': estadisticas_estado,
            'por_categoria': estadisticas_categoria,
            'por_gravedad': estadisticas_gravedad,
            'categoria_mas_reportes': {
                'categoria': categoria_mas_reportes[0] if categoria_mas_reportes else None,
                'cantidad': categoria_mas_reportes[1] if categoria_mas_reportes else 0
            },
            'solucionados': solucionados,
            'no_solucionados': no_solucionados,
            'activos': activos,
            'tasa_solucion': round((solucionados / total_reportes * 100) if total_reportes > 0 else 0, 2)
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(estadisticas)
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

