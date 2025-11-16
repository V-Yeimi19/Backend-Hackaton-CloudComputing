# 🏗️ Arquitectura de Microservicios - AlertaUTEC

## 📊 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    MICROSERVICIO REPORTES                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Gateway                                         │   │
│  │  /reportes/*                                         │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐   │
│  │  Lambda Functions (8 funciones)                      │   │
│  │  - crearReporte                                      │   │
│  │  - obtenerReporte                                    │   │
│  │  - listarReportes                                    │   │
│  │  - actualizarReporte                                 │   │
│  │  - eliminarReporte                                   │   │
│  │  - actualizarEstadoReporte                           │   │
│  │  - asignarResponsables                               │   │
│  │  - obtenerResponsables                              │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐   │
│  │  DynamoDB Tables                                      │   │
│  │  - Reporte (con Stream habilitado)                  │   │
│  │  - AsignacionResponsables                            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ DynamoDB Stream
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 MICROSERVICIO ANALÍTICA                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Gateway                                         │   │
│  │  /analitica/*                                        │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐   │
│  │  Lambda Functions (5 funciones)                       │   │
│  │  - obtenerReportesActivos                            │   │
│  │  - filtrarReportes                                   │   │
│  │  - obtenerEstadisticas                                │   │
│  │  - consultarAthena                                   │   │
│  │  - ingestaDynamoDBToS3 (triggered by Stream)        │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐   │
│  │  S3 Bucket (Analytics)                                │   │
│  │  └─ reportes/year=YYYY/month=MM/day=DD/              │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐   │
│  │  AWS Glue                                             │   │
│  │  - Database                                           │   │
│  │  - Crawler                                            │   │
│  └──────────────┬───────────────────────────────────────┘   │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐   │
│  │  AWS Athena                                           │   │
│  │  - Workgroup                                          │   │
│  │  - SQL Queries                                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Flujo de Datos

### 1. Creación de Reporte
```
Usuario → API Gateway (Reportes) → Lambda (crearReporte) → DynamoDB
```

### 2. Ingesta Automática
```
DynamoDB Stream → Lambda (ingestaDynamoDBToS3) → S3 (particionado)
```

### 3. Catalogación
```
S3 → Glue Crawler → Glue Data Catalog
```

### 4. Consultas Analíticas
```
Usuario → API Gateway (Analítica) → Lambda → DynamoDB (directo)
Usuario → API Gateway (Analítica) → Lambda → Athena → S3 (vía Glue)
```

## 🎯 Separación de Responsabilidades

### Microservicio Reportes
- **Responsabilidad:** Gestión de datos transaccionales
- **Tecnologías:** DynamoDB, Lambda, API Gateway
- **Patrón:** CRUD tradicional
- **Escalabilidad:** Por número de reportes creados

### Microservicio Analítica
- **Responsabilidad:** Análisis y procesamiento de datos
- **Tecnologías:** S3, Glue, Athena, Lambda, API Gateway
- **Patrón:** ETL (Extract, Transform, Load)
- **Escalabilidad:** Por volumen de datos analizados

## 🔗 Comunicación Entre Servicios

### Sincrónica (Directa)
- **Analítica → DynamoDB:** Las funciones de analítica leen directamente de DynamoDB
- **No hay comunicación directa entre servicios** (desacoplados)

### Asíncrona (Event-Driven)
- **DynamoDB Stream → Ingesta:** Eventos de DynamoDB activan la ingesta automáticamente

## 📦 Recursos Compartidos

### Tablas DynamoDB
- Ambos servicios usan las mismas tablas
- Solo el microservicio-reportes las crea
- El microservicio-analitica solo las lee

### Nombres de Recursos
- Usan el mismo prefijo: `alerta-utec-`
- Diferentes sufijos según el servicio
- Mismo `stage` para mantener consistencia

## 🚀 Ventajas de esta Arquitectura

1. **Despliegue Independiente**
   - Actualizar reportes no afecta analítica
   - Actualizar analítica no afecta reportes

2. **Escalabilidad Independiente**
   - Reportes escala con tráfico de creación
   - Analítica escala con volumen de datos

3. **Equipos Paralelos**
   - Equipo A: Reportes
   - Equipo B: Analítica

4. **Tecnologías Específicas**
   - Cada servicio usa las tecnologías más adecuadas
   - No hay compromisos entre necesidades diferentes

5. **Mantenibilidad**
   - Código más organizado
   - Responsabilidades claras
   - Más fácil de entender y modificar

## ⚠️ Consideraciones

### Orden de Despliegue
1. **Primero:** microservicio-reportes (crea tablas)
2. **Segundo:** microservicio-analitica (usa tablas existentes)

### URLs Diferentes
- Cada servicio tiene su propia URL de API Gateway
- Considerar usar Custom Domain para unificar

### Monitoreo
- CloudWatch separado por servicio
- Métricas independientes
- Logs separados

## 🔮 Evolución Futura

### Posibles Mejoras
1. **API Gateway Custom Domain** - Unificar URLs
2. **Service Mesh** - Si se agregan más servicios
3. **EventBridge** - Para comunicación asíncrona más compleja
4. **SQS/SNS** - Para desacoplamiento adicional
5. **Caché Distribuido** - ElastiCache compartido

