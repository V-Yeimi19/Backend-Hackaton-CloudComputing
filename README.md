# AlertaUTEC - Backend Serverless

Backend completamente serverless para la plataforma AlertaUTEC, desarrollado para la hackatón del curso de Cloud Computing durante el ciclo 2025-2.

## Descripción

AlertaUTEC es una plataforma que permite reportar, gestionar y dar seguimiento a incidentes dentro del campus universitario en tiempo real. Este backend implementa:

- **Gestión de Reportes**: CRUD completo para reportes de incidentes
- **Panel Administrativo**: Funciones de analítica y visualización de datos
- **Ingesta de Datos**: Pipeline automatizado DynamoDB → S3 → Glue → Athena

## Arquitectura

- **Runtime**: Python 3.13
- **Framework**: Serverless Framework
- **Base de datos**: DynamoDB (tablas `Reporte` y `AsignacionResponsables`)
- **API**: API Gateway con integración Lambda
- **Almacenamiento**: S3 para datos de analítica
- **Catalogación**: AWS Glue
- **Consultas SQL**: AWS Athena
- **Event Processing**: DynamoDB Streams

## Estructura del Proyecto

```
Backend-Hackaton-CloudComputing/
├── reportes/
│   ├── crearReporte.py
│   ├── obtenerReporte.py
│   ├── listarReportes.py
│   ├── actualizarReporte.py
│   ├── eliminarReporte.py
│   ├── actualizarEstadoReporte.py
│   ├── asignarResponsables.py
│   ├── obtenerResponsables.py
│   └── __init__.py
├── analitica/
│   ├── obtenerReportesActivos.py
│   ├── filtrarReportes.py
│   ├── obtenerEstadisticas.py
│   ├── consultarAthena.py
│   └── __init__.py
├── ingesta/
│   ├── ingestaDynamoDBToS3.py
│   └── __init__.py
├── serverless.yml
├── requirements.txt
├── .gitignore
└── README.md
```

## Tablas DynamoDB

### Tabla: Reporte

- **Partition Key**: `id` (String) - UUID único del reporte
- **Atributos**:
  - `UsuarioId` (String): ID del usuario que creó el reporte
  - `DescripcionCorta` (String): Descripción breve del incidente
  - `Categoria` (String): Categoría del incidente
    - Limpieza y desorden
    - Fugas
    - Calidad del inmobiliario
    - Calidad de lo servicios (Luz, Internet, Agua)
    - Aulas cerradas
    - Objeto perdido
  - `Gravedad` (String): Nivel de urgencia (debil, moderado, fuerte)
  - `Lugar` (String): Ubicación del incidente
  - `Estado` (String): Estado del reporte (PENDIENTE, EN ARREGLO, SOLUCIONADO)
  - `FechaCreacion` (String): Timestamp ISO de creación
  - `FechaActualizacion` (String): Timestamp ISO de última actualización
- **Stream**: Habilitado (NEW_AND_OLD_IMAGES)

### Tabla: AsignacionResponsables

- **Partition Key**: `ReporteId` (String) - ID del reporte
- **Atributos**:
  - `TrabajadoresId` (List): Lista de IDs de trabajadores asignados

## Endpoints API

### Reportes

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/reportes` | Crear un nuevo reporte |
| GET | `/reportes` | Listar todos los reportes (con filtros opcionales) |
| GET | `/reportes/{id}` | Obtener un reporte específico |
| PUT | `/reportes/{id}` | Actualizar un reporte |
| DELETE | `/reportes/{id}` | Eliminar un reporte |
| PATCH | `/reportes/{id}/estado` | Actualizar el estado de un reporte |
| POST | `/reportes/{id}/asignar` | Asignar responsables a un reporte |
| GET | `/reportes/{id}/responsables` | Obtener responsables asignados a un reporte |

### Analítica / Panel Administrativo

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/analitica/reportes-activos` | Obtener todos los reportes activos (PENDIENTE, EN ARREGLO) |
| GET | `/analitica/filtrar` | Filtrar reportes por múltiples criterios |
| GET | `/analitica/estadisticas` | Obtener estadísticas generales |
| POST | `/analitica/consultar` | Ejecutar consulta SQL personalizada en Athena |

## Instalación y Despliegue

### Requisitos Previos

- Node.js y npm instalados
- Serverless Framework: `npm install -g serverless`
- Credenciales AWS configuradas
- Python 3.13
- Rol IAM `LabRole` con permisos para:
  - DynamoDB (lectura, escritura, streams)
  - S3 (lectura, escritura)
  - Glue (lectura, escritura)
  - Athena (ejecutar consultas)

### Despliegue

```bash
# Instalar dependencias
npm install

# Desplegar a AWS
serverless deploy

# Desplegar solo una función específica
serverless deploy function -f crearReporte

# Ver logs en tiempo real
serverless logs -f crearReporte -t
```

## Ejemplos de Uso

### Crear un Reporte

```bash
curl -X POST https://your-api-url/reportes \
  -H "Content-Type: application/json" \
  -d '{
    "UsuarioId": "USER123",
    "DescripcionCorta": "Fuga de agua en el baño del segundo piso",
    "Categoria": "Fugas",
    "Gravedad": "fuerte",
    "Lugar": "Edificio A, Segundo piso, Baño 201"
  }'
```

### Listar Reportes con Filtros

```bash
# Por estado
curl "https://your-api-url/reportes?Estado=PENDIENTE"

# Por categoría
curl "https://your-api-url/reportes?Categoria=Fugas"

# Por usuario
curl "https://your-api-url/reportes?UsuarioId=USER123"
```

### Actualizar Estado de un Reporte

```bash
curl -X PATCH https://your-api-url/reportes/{id}/estado \
  -H "Content-Type: application/json" \
  -d '{
    "Estado": "EN ARREGLO"
  }'
```

### Asignar Responsables

```bash
curl -X POST https://your-api-url/reportes/{id}/asignar \
  -H "Content-Type: application/json" \
  -d '{
    "TrabajadoresId": ["WORKER001", "WORKER002"]
  }'
```

### Obtener Estadísticas

```bash
curl https://your-api-url/analitica/estadisticas
```

Respuesta ejemplo:
```json
{
  "total_reportes": 150,
  "por_estado": {
    "PENDIENTE": 45,
    "EN ARREGLO": 30,
    "SOLUCIONADO": 75
  },
  "por_categoria": {
    "Fugas": 50,
    "Limpieza y desorden": 40,
    "Calidad del inmobiliario": 30,
    ...
  },
  "categoria_mas_reportes": {
    "categoria": "Fugas",
    "cantidad": 50
  },
  "solucionados": 75,
  "no_solucionados": 75,
  "activos": 75,
  "tasa_solucion": 50.0
}
```

### Consultar Athena

```bash
curl -X POST https://your-api-url/analitica/consultar \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT categoria, COUNT(*) as total FROM reportes GROUP BY categoria ORDER BY total DESC"
  }'
```

## Pipeline de Ingesta de Datos

El sistema implementa un pipeline automatizado para análisis de datos:

1. **DynamoDB Streams**: Captura cambios en la tabla `Reporte` (INSERT, MODIFY)
2. **Lambda (ingestaDynamoDBToS3)**: Procesa los eventos del stream y guarda los datos en S3 con particionado por fecha/hora
3. **S3**: Almacena los datos en formato JSON particionado: `reportes/year=YYYY/month=MM/day=DD/hour=HH/`
4. **Glue Crawler**: Catalogación automática de los datos en S3
5. **Athena**: Permite ejecutar consultas SQL sobre los datos catalogados

### Estructura de Datos en S3

```
s3://alerta-utec-backend-analytics-dev/
└── reportes/
    └── year=2025/
        └── month=01/
            └── day=15/
                └── hour=14/
                    └── 2025-01-15T14:30:00-uuid.json
```

## Validaciones Implementadas

### Reportes

- Campos requeridos: `UsuarioId`, `DescripcionCorta`, `Categoria`, `Gravedad`, `Lugar`
- Categoría debe ser una de las 6 categorías válidas
- Gravedad debe ser: `debil`, `moderado`, o `fuerte`
- Estado debe ser: `PENDIENTE`, `EN ARREGLO`, o `SOLUCIONADO`

### Asignaciones

- `TrabajadoresId` debe ser una lista
- El reporte debe existir antes de asignar responsables

## Notas Técnicas

- Las funciones Lambda tienen 256MB de memoria y 30 segundos de timeout (excepto ingesta que tiene 512MB y 60s)
- CORS está habilitado en todos los endpoints HTTP
- Las tablas DynamoDB se crean automáticamente con el despliegue
- El bucket S3 se crea automáticamente con versionado habilitado
- El Glue Database y Crawler se crean automáticamente
- El Athena Workgroup se crea automáticamente
- DynamoDB Streams está habilitado en la tabla `Reporte` para la ingesta

## Próximos Pasos

- Implementar índices GSI en DynamoDB para consultas más eficientes
- Agregar autenticación y autorización (Cognito)
- Implementar WebSockets para actualizaciones en tiempo real
- Integrar Apache Airflow para orquestación de tareas
- Implementar visualizaciones con AWS SageMaker

## Licencia

Ver archivo LICENSE para más detalles.
