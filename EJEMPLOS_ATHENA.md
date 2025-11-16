# Ejemplos de Consultas SQL para Athena

Este documento contiene ejemplos de consultas SQL que puedes ejecutar usando el endpoint `/analitica/consultar` para analizar los datos de reportes almacenados en S3.

## Nota Importante

Antes de ejecutar consultas, asegúrate de que:
1. El Glue Crawler haya ejecutado al menos una vez para catalogar los datos
2. Los datos hayan sido ingeridos en S3 desde DynamoDB

## Ejemplos de Consultas

### 1. Contar reportes por categoría

```sql
SELECT categoria, COUNT(*) as total
FROM reportes
GROUP BY categoria
ORDER BY total DESC
```

### 2. Reportes por estado

```sql
SELECT estado, COUNT(*) as cantidad
FROM reportes
GROUP BY estado
```

### 3. Categoría con más reportes

```sql
SELECT categoria, COUNT(*) as total
FROM reportes
GROUP BY categoria
ORDER BY total DESC
LIMIT 1
```

### 4. Reportes solucionados vs no solucionados

```sql
SELECT 
  CASE 
    WHEN estado = 'SOLUCIONADO' THEN 'Solucionados'
    ELSE 'No Solucionados'
  END as tipo,
  COUNT(*) as cantidad
FROM reportes
GROUP BY 
  CASE 
    WHEN estado = 'SOLUCIONADO' THEN 'Solucionados'
    ELSE 'No Solucionados'
  END
```

### 5. Reportes por gravedad

```sql
SELECT gravedad, COUNT(*) as total
FROM reportes
GROUP BY gravedad
ORDER BY 
  CASE gravedad
    WHEN 'fuerte' THEN 1
    WHEN 'moderado' THEN 2
    WHEN 'debil' THEN 3
  END
```

### 6. Reportes activos (pendientes y en arreglo)

```sql
SELECT *
FROM reportes
WHERE estado IN ('PENDIENTE', 'EN ARREGLO')
ORDER BY fechacreacion DESC
```

### 7. Tasa de solución por categoría

```sql
SELECT 
  categoria,
  COUNT(*) as total,
  SUM(CASE WHEN estado = 'SOLUCIONADO' THEN 1 ELSE 0 END) as solucionados,
  ROUND(SUM(CASE WHEN estado = 'SOLUCIONADO' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as tasa_solucion
FROM reportes
GROUP BY categoria
ORDER BY tasa_solucion DESC
```

### 8. Lugares con más reportes

```sql
SELECT lugar, COUNT(*) as total_reportes
FROM reportes
GROUP BY lugar
ORDER BY total_reportes DESC
LIMIT 10
```

### 9. Reportes por mes

```sql
SELECT 
  DATE_FORMAT(date_parse(fechacreacion, '%Y-%m-%dT%H:%i:%s'), '%Y-%m') as mes,
  COUNT(*) as total
FROM reportes
GROUP BY DATE_FORMAT(date_parse(fechacreacion, '%Y-%m-%dT%H:%i:%s'), '%Y-%m')
ORDER BY mes DESC
```

### 10. Reportes urgentes (fuerte gravedad) no solucionados

```sql
SELECT *
FROM reportes
WHERE gravedad = 'fuerte' 
  AND estado != 'SOLUCIONADO'
ORDER BY fechacreacion DESC
```

## Uso con cURL

```bash
curl -X POST https://your-api-url/analitica/consultar \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT categoria, COUNT(*) as total FROM reportes GROUP BY categoria ORDER BY total DESC"
  }'
```

## Notas sobre el Schema

El schema de la tabla `reportes` en Glue se genera automáticamente cuando el Crawler ejecuta. Los nombres de las columnas pueden variar según cómo se almacenen los datos en JSON. Asegúrate de verificar el schema real ejecutando:

```sql
DESCRIBE reportes
```

O consultando la base de datos en AWS Glue Console.

