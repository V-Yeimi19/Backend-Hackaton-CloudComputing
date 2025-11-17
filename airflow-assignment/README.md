# Airflow - Asignación Automática de Incidentes

## 📋 Descripción

Sistema de asignación automática de incidentes a empleados usando Apache Airflow. El flujo detecta nuevos incidentes sin asignar y los asigna automáticamente a empleados disponibles de la categoría correspondiente.

## 🔄 Flujo de Trabajo

1. **Detección**: Airflow detecta incidentes sin asignar cada 2 minutos
2. **Búsqueda**: Busca empleados disponibles de la categoría/área del incidente
3. **Asignación**: Asigna el incidente al primer empleado disponible (máximo 3 incidentes pendientes)
4. **Reintento**: Si no hay empleados disponibles, espera y reintenta

## 📦 Componentes

### Lambdas

1. **asignar_incidente_empleado.py**
   - Asigna un incidente a un empleado específico
   - Endpoint: `PUT /incidentes/{id}/asignar-empleado`
   - Body: `{ "incidenteId": "uuid", "empleadoEmail": "email@example.com" }`

2. **listar_incidentes_empleado.py**
   - Permite a un empleado ver sus incidentes
   - Endpoint: `GET /incidentes/empleado?empleadoEmail=xxx&tipo=asignados|disponibles|todos`
   - Tipos:
     - `asignados`: Solo incidentes asignados a él
     - `disponibles`: Incidentes de su área sin asignar
     - `todos`: Todos los incidentes de su área

### DAG de Airflow

**dags/asignacion_automatica.py**
- Se ejecuta cada 2 minutos
- Tareas:
  1. `obtener_incidentes_sin_asignar`: Obtiene incidentes pendientes
  2. `buscar_empleado_disponible`: Busca empleados disponibles
  3. `asignar_incidentes`: Llama al Lambda para asignar

## 🚀 Despliegue

### 1. Desplegar Lambdas

```bash
cd airflow-assignment
serverless deploy
```

### 2. Airflow Local (Docker Compose)

```bash
# Configurar variables de entorno
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export LAMBDA_API_URL=https://your-api.execute-api.us-east-1.amazonaws.com/production

# Iniciar Airflow
docker-compose up -d

# Acceder a la UI
# http://localhost:8080
# Usuario: admin
# Password: admin
```

### 3. Airflow en AWS (Fargate)

#### Construir y subir imagen Docker

```bash
# Autenticarse en ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Construir imagen
docker build -t airflow-alerta-utec .

# Taggear
docker tag airflow-alerta-utec:latest ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/airflow-alerta-utec:latest

# Subir
docker push ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/airflow-alerta-utec:latest
```

#### Crear ECS Cluster y Task Definition

```bash
# Crear cluster
aws ecs create-cluster --cluster-name airflow-alerta-utec

# Registrar task definition (editar ecs-task-definition.json primero)
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Crear servicio
aws ecs create-service \
  --cluster airflow-alerta-utec \
  --service-name airflow-webserver \
  --task-definition airflow-alerta-utec \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## 🔧 Configuración

### Variables de Entorno (Airflow)

Configurar en Airflow UI (Admin > Variables) o en `docker-compose.yml`:

- `INCIDENTES_TABLE`: Incidentes
- `USUARIOS_TABLE`: tabla_usuarios
- `LAMBDA_API_URL`: URL del API Gateway
- `AWS_ACCESS_KEY_ID`: Tu AWS Access Key
- `AWS_SECRET_ACCESS_KEY`: Tu AWS Secret Key
- `AWS_DEFAULT_REGION`: us-east-1

### Estructura de Datos

**Incidentes** (DynamoDB):
- `id`: UUID del incidente
- `estado`: "Reportado", "Pendiente", "En atencion", "Finalizado"
- `areaResponsable`: Área responsable (ej: "Limpieza", "Seguridad")
- `asignadoA`: Email del empleado asignado (opcional)
- `asignadoEn`: Fecha de asignación (opcional)

**Usuarios** (DynamoDB):
- `email`: Email del usuario
- `rol`: "trabajador", "administrativo", "usuario"
- `area`: Área de trabajo del empleado

## 📝 Uso

### Ver Incidentes Asignados (Empleado)

```bash
curl "https://api.example.com/incidentes/empleado?empleadoEmail=empleado@example.com&tipo=asignados"
```

### Ver Incidentes Disponibles (Empleado)

```bash
curl "https://api.example.com/incidentes/empleado?empleadoEmail=empleado@example.com&tipo=disponibles"
```

### Actualizar Estado de Incidente (Empleado)

```bash
curl -X PUT "https://api.example.com/incidentes/{id}/estado" \
  -H "Content-Type: application/json" \
  -d '{"estado": "En atencion"}'
```

## 🔍 Monitoreo

- **Airflow UI**: Ver logs y estado de los DAGs
- **CloudWatch**: Logs de los Lambdas
- **DynamoDB**: Ver asignaciones en tiempo real

## 📚 Referencias

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [AWS ECS Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Serverless Framework](https://www.serverless.com/framework/docs)

