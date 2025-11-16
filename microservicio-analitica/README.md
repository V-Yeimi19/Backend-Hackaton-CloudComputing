# Microservicio de Analítica - AlertaUTEC

Microservicio independiente para análisis de datos e ingesta desde DynamoDB a S3.

## 🎯 Responsabilidades

- ✅ Panel administrativo con reportes activos
- ✅ Filtrado avanzado de reportes
- ✅ Estadísticas generales
- ✅ Consultas SQL en Athena
- ✅ Ingesta automática de datos a S3

## 📁 Estructura

```
microservicio-analitica/
├── serverless.yml          # Configuración del servicio
├── requirements.txt        # Dependencias Python
├── analitica/             # Funciones Lambda de analítica
│   ├── obtenerReportesActivos.py
│   ├── filtrarReportes.py
│   ├── obtenerEstadisticas.py
│   └── consultarAthena.py
└── ingesta/               # Funciones Lambda de ingesta
    └── ingestaDynamoDBToS3.py
```

## 🚀 Despliegue

**⚠️ IMPORTANTE:** Desplegar **después** del microservicio-reportes

```bash
cd microservicio-analitica
pip install -r requirements.txt
serverless deploy
```

## 📡 Endpoints

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/analitica/reportes-activos` | Obtener reportes activos |
| GET | `/analitica/filtrar` | Filtrar reportes |
| GET | `/analitica/estadisticas` | Obtener estadísticas |
| POST | `/analitica/consultar` | Consultar Athena |

## 🗄️ Recursos Creados

- **S3 Bucket:** `alerta-utec-analytics-{stage}`
- **Glue Database:** `alerta-utec-analytics-db`
- **Glue Crawler:** `alerta-utec-analitica-crawler-{stage}`
- **Athena Workgroup:** `alerta-utec-analytics-workgroup`

## ⚙️ Variables de Entorno

- `REPORTES_TABLE`: Nombre de la tabla de reportes (compartida)
- `ASIGNACIONES_TABLE`: Nombre de la tabla de asignaciones (compartida)
- `S3_BUCKET_ANALYTICS`: Bucket S3 para analytics
- `GLUE_DATABASE`: Base de datos de Glue
- `ATHENA_WORKGROUP`: Workgroup de Athena

## 🔗 Dependencias

Este microservicio **depende** de:
- ✅ Tablas DynamoDB creadas por `microservicio-reportes`
- ✅ Stream de DynamoDB habilitado en la tabla de reportes

## 📊 Pipeline de Datos

1. **DynamoDB Stream** → Detecta cambios en tabla de reportes
2. **Lambda (ingestaDynamoDBToS3)** → Guarda datos en S3 particionado
3. **Glue Crawler** → Catalogación automática de datos
4. **Athena** → Consultas SQL sobre datos catalogados

