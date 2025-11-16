# Guía Completa de Despliegue y Uso - AlertaUTEC

## 📋 Tabla de Contenidos

1. [Preparación](#preparación)
2. [Despliegue](#despliegue)
3. [Verificación](#verificación)
4. [Uso desde Postman](#uso-desde-postman)
5. [Próximos Pasos](#próximos-pasos)

---

## 🔧 Preparación

### 1. Verificar Requisitos

```bash
# Verificar Node.js y npm
node --version
npm --version

# Verificar Python
python --version  # Debe ser 3.13

# Verificar Serverless Framework
serverless --version

# Verificar credenciales AWS
aws sts get-caller-identity
```

### 2. Instalar Dependencias

```bash
# Navegar al directorio del proyecto
cd Backend-Hackaton-CloudComputing

# Instalar dependencias de Python
pip install -r requirements.txt

# Instalar dependencias de Serverless (si es necesario)
npm install
```

### 3. Verificar Configuración AWS

Asegúrate de tener:
- ✅ Credenciales AWS configuradas (`~/.aws/credentials` o variables de entorno)
- ✅ Rol IAM `LabRole` con permisos para:
  - DynamoDB (crear tablas, leer, escribir, streams)
  - S3 (crear buckets, leer, escribir)
  - Glue (crear databases, crawlers)
  - Athena (crear workgroups, ejecutar consultas)
  - Lambda (crear funciones)
  - API Gateway (crear APIs)
  - CloudFormation (crear stacks)

---

## 🚀 Despliegue

### Paso 1: Desplegar Todo el Stack

```bash
# Desde el directorio Backend-Hackaton-CloudComputing
serverless deploy
```

Este comando desplegará:
- ✅ Tablas DynamoDB (Reporte, AsignacionResponsables)
- ✅ Bucket S3 para analytics
- ✅ Glue Database y Crawler
- ✅ Athena Workgroup
- ✅ Todas las funciones Lambda (reportes, analítica, ingesta)
- ✅ API Gateway con todos los endpoints

**Tiempo estimado:** 3-5 minutos

### Paso 2: Guardar la URL de la API

Al finalizar el despliegue, verás algo como:

```
endpoints:
  POST - https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev/reportes
  GET - https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev/reportes
  ...
```

**⚠️ IMPORTANTE:** Copia esta URL base: `https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev`

### Paso 3: Verificar Recursos Creados

```bash
# Ver información del stack desplegado
serverless info

# Ver logs de una función específica
serverless logs -f crearReporte --tail
```

---

## ✅ Verificación

### 1. Verificar Tablas DynamoDB

```bash
# Listar tablas creadas
aws dynamodb list-tables

# Deberías ver:
# - alerta-utec-backend-Reporte-dev
# - alerta-utec-backend-AsignacionResponsables-dev
```

### 2. Verificar Bucket S3

```bash
# Listar buckets
aws s3 ls

# Deberías ver:
# - alerta-utec-backend-analytics-dev
```

### 3. Verificar Funciones Lambda

```bash
# Listar funciones
aws lambda list-functions --query 'Functions[?contains(FunctionName, `alerta-utec`)].FunctionName'

# Deberías ver todas las funciones:
# - alerta-utec-backend-dev-crearReporte
# - alerta-utec-backend-dev-obtenerReporte
# - ... (y todas las demás)
```

### 4. Verificar Glue Database

```bash
# Listar databases de Glue
aws glue get-databases

# Deberías ver:
# - alerta-utec-backend-analytics-db
```

---

## 📮 Uso desde Postman

### Paso 1: Importar Colección

1. Abre Postman
2. Click en **"Import"** (botón superior izquierdo)
3. Selecciona el archivo: `AlertaUTEC-API.postman_collection.json`
4. También importa: `AlertaUTEC-API.postman_environment.json`

### Paso 2: Configurar Variables de Entorno

1. En Postman, click en **"Environments"** (lateral izquierdo)
2. Selecciona **"AlertaUTEC - Development"**
3. Actualiza la variable `base_url` con tu URL real:
   ```
   https://abc123xyz.execute-api.us-east-1.amazonaws.com/dev
   ```
   (Reemplaza `abc123xyz` con tu ID real)

### Paso 3: Probar Endpoints

#### 🔹 **Flujo Básico: Crear y Consultar Reportes**

1. **Crear un Reporte:**
   - Selecciona: `Reportes` → `Crear Reporte`
   - Click en **"Send"**
   - **Guarda el `id` del reporte** de la respuesta

2. **Obtener el Reporte Creado:**
   - Selecciona: `Reportes` → `Obtener Reporte`
   - En la URL, reemplaza `{{reporte_id}}` con el ID que guardaste
   - Click en **"Send"**

3. **Listar Todos los Reportes:**
   - Selecciona: `Reportes` → `Listar Reportes`
   - Click en **"Send"**

#### 🔹 **Flujo Completo: Gestión de Reportes**

1. **Crear varios reportes** con diferentes categorías y gravedades
2. **Actualizar un reporte:**
   - `Reportes` → `Actualizar Reporte`
   - Modifica el body según necesites
3. **Cambiar estado:**
   - `Reportes` → `Actualizar Estado Reporte`
   - Body: `{"Estado": "EN ARREGLO"}`
4. **Asignar responsables:**
   - `Asignaciones` → `Asignar Responsables`
   - Body: `{"TrabajadoresId": ["WORKER001", "WORKER002"]}`

#### 🔹 **Panel Administrativo / Analítica**

1. **Ver Reportes Activos:**
   - `Analítica` → `Obtener Reportes Activos`
   - Muestra solo reportes con estado PENDIENTE o EN ARREGLO

2. **Filtrar Reportes:**
   - `Analítica` → `Filtrar Reportes`
   - Habilita los query parameters que necesites (Estado, Categoria, Gravedad, Lugar)

3. **Ver Estadísticas:**
   - `Analítica` → `Obtener Estadísticas`
   - Obtiene estadísticas generales del sistema

4. **Consultar Athena (después de ingesta):**
   - `Analítica` → `Consultar Athena`
   - Body ejemplo:
     ```json
     {
       "query": "SELECT categoria, COUNT(*) as total FROM reportes GROUP BY categoria ORDER BY total DESC"
     }
     ```

### Paso 4: Probar la Ingesta

La ingesta se activa automáticamente cuando:
- ✅ Creas un nuevo reporte
- ✅ Actualizas un reporte existente

**Para verificar que funciona:**

1. Crea un nuevo reporte desde Postman
2. Espera unos segundos
3. Verifica en S3:
   ```bash
   aws s3 ls s3://alerta-utec-backend-analytics-dev/reportes/ --recursive
   ```
   Deberías ver archivos JSON organizados por fecha/hora

4. Ejecuta el Glue Crawler manualmente (primera vez):
   ```bash
   aws glue start-crawler --name alerta-utec-backend-crawler-dev
   ```

5. Espera a que termine (puedes verificar el estado):
   ```bash
   aws glue get-crawler --name alerta-utec-backend-crawler-dev --query 'Crawler.State'
   ```

6. Una vez que el crawler termine, puedes consultar Athena desde Postman

---

## 🎯 Próximos Pasos Sugeridos

### 1. **Mejoras Inmediatas (Corto Plazo)**

#### a) Índices GSI en DynamoDB
Para mejorar el rendimiento de consultas:

```yaml
# Agregar en serverless.yml, dentro de ReporteTable
GlobalSecondaryIndexes:
  - IndexName: EstadoIndex
    KeySchema:
      - AttributeName: Estado
        KeyType: HASH
    Projection:
      ProjectionType: ALL
  - IndexName: CategoriaIndex
    KeySchema:
      - AttributeName: Categoria
        KeyType: HASH
    Projection:
      ProjectionType: ALL
```

#### b) Validación de Entrada Mejorada
- Agregar validación de formato de UUID para `UsuarioId`
- Validar que `Lugar` no esté vacío
- Agregar límites de longitud para campos de texto

#### c) Manejo de Errores Mejorado
- Logs estructurados con CloudWatch
- Códigos de error más específicos
- Mensajes de error más descriptivos

### 2. **Funcionalidades Adicionales (Mediano Plazo)**

#### a) Autenticación y Autorización
- Integrar AWS Cognito para autenticación
- Control de acceso basado en roles (Comunidad vs Administrativo)
- Validar tokens JWT en cada Lambda

#### b) Notificaciones
- SNS para enviar notificaciones cuando se crea un reporte
- Email/SMS para reportes de gravedad "fuerte"
- Notificaciones cuando cambia el estado de un reporte

#### c) WebSockets para Tiempo Real
- Actualizaciones en tiempo real del panel administrativo
- Notificaciones push cuando se crean nuevos reportes
- Sincronización automática sin recargar página

### 3. **Integración con Airflow (Largo Plazo)**

#### a) Configurar Airflow en EC2
```bash
# Instalar Airflow
pip install apache-airflow
pip install apache-airflow-providers-amazon

# Inicializar
airflow db init
airflow users create --username admin --role Admin --email admin@example.com
```

#### b) Crear DAGs para:
- Análisis batch diario de reportes
- Generación de reportes automáticos
- Limpieza de datos antiguos
- Agregaciones complejas

### 4. **Optimizaciones de Rendimiento**

#### a) Caché
- Usar ElastiCache (Redis) para cachear estadísticas frecuentes
- Cachear resultados de consultas Athena

#### b) Optimización de Consultas
- Particionar datos en S3 por categoría además de fecha
- Usar formato Parquet en lugar de JSON para mejor compresión

### 5. **Monitoreo y Observabilidad**

#### a) CloudWatch Dashboards
- Métricas de reportes creados por día
- Tiempo promedio de resolución
- Categorías más reportadas

#### b) Alertas
- Alertar si hay más de X reportes urgentes sin resolver
- Alertar si el tiempo de respuesta de Lambda es alto

### 6. **Testing**

#### a) Tests Unitarios
```python
# Crear tests/ para cada función Lambda
# Usar pytest y moto para mockear AWS
```

#### b) Tests de Integración
- Probar flujo completo: crear reporte → ingesta → consulta Athena

### 7. **Documentación Adicional**

- Documentación de API con Swagger/OpenAPI
- Diagramas de arquitectura
- Guías de troubleshooting

---

## 🔍 Troubleshooting

### Problema: Error al desplegar

```bash
# Ver logs detallados
serverless deploy --verbose

# Verificar credenciales
aws sts get-caller-identity
```

### Problema: Lambda no puede acceder a DynamoDB

- Verificar que el rol `LabRole` tenga permisos de DynamoDB
- Verificar que el nombre de la tabla sea correcto

### Problema: Glue Crawler no encuentra datos

- Verificar que los datos estén en S3
- Verificar la ruta del crawler: `s3://bucket-name/reportes/`
- Ejecutar el crawler manualmente y revisar logs

### Problema: Athena no encuentra tablas

- Verificar que el Glue Crawler haya terminado exitosamente
- Verificar que la base de datos existe en Glue
- Verificar permisos del rol para Athena

---

## 📊 Checklist de Despliegue

- [ ] Credenciales AWS configuradas
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] `serverless deploy` ejecutado exitosamente
- [ ] URL de API copiada y configurada en Postman
- [ ] Al menos un reporte creado exitosamente
- [ ] Verificado que los datos están en S3
- [ ] Glue Crawler ejecutado al menos una vez
- [ ] Consulta Athena funciona correctamente
- [ ] Estadísticas se obtienen correctamente

---

## 🎓 Recursos Adicionales

- [Documentación Serverless Framework](https://www.serverless.com/framework/docs)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [Athena SQL Reference](https://docs.aws.amazon.com/athena/latest/ug/ddl-sql-reference.html)

