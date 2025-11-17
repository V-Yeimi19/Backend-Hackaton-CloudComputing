# 📋 URLs de APIs Desplegadas

## APIs Disponibles

Después de desplegar todos los servicios, estas son las URLs disponibles:

### 1. Seguridad y Usuarios
- **URL Base**: `https://ejxa6zzhk3.execute-api.us-east-1.amazonaws.com`
- **Endpoints**:
  - `POST /usuarios` - Crear usuario
  - `POST /login` - Login de usuario

### 2. Incidentes
- **URL Base**: `https://jdbbruotf8.execute-api.us-east-1.amazonaws.com`
- **Endpoints**:
  - `POST /incidentes` - Crear incidente
  - `DELETE /incidentes/{id}` - Eliminar incidente
  - `POST /validar-token` - Validar token

### 3. Actualización de Incidentes
- **URL Base**: `https://rqa3td2hlc.execute-api.us-east-1.amazonaws.com`
- **Endpoints**:
  - `PUT /incidentes/{id}/estado` - Actualizar estado de incidente

### 4. Panel de Administración
- **URL Base**: `https://sw8gon2h0d.execute-api.us-east-1.amazonaws.com`
- **Endpoints**:
  - `GET /admin/incidentes` - Listar incidentes activos
  - `GET /admin/incidentes/resumen` - Resumen de incidentes

### 5. Tiempo Real (WebSocket)
- **URL WebSocket**: `wss://ngvi5oamc1.execute-api.us-east-1.amazonaws.com/prod`

### 6. Asignación Automática (Airflow) ⚠️
- **URL Base**: `https://{api-id}.execute-api.us-east-1.amazonaws.com` (después de desplegar)
- **Endpoints**:
  - `PUT /incidentes/{id}/asignar-empleado` - Asignar incidente a empleado
  - `GET /incidentes/empleado` - Listar incidentes de empleado

## 🔧 Configuración para Airflow

### Para el archivo `.env`:

1. **LAMBDA_API_URL**: 
   - **Actual**: Dejar como placeholder hasta desplegar `airflow-assignment`
   - **Después de desplegar**: Usar la URL que aparezca en el output de `serverless deploy`
   - **Ejemplo**: `https://abc123xyz.execute-api.us-east-1.amazonaws.com`

2. **LAMBDA_ASIGNAR_FUNCTION**:
   - **Formato**: `alerta-utec-airflow-assignment-prod-asignarIncidenteEmpleado`
   - **Nota**: El stage es `prod` (no `production`)

### Pasos para obtener la URL después de desplegar:

```bash
cd airflow-assignment
serverless deploy

# Buscar en el output:
# HttpApiUrl: https://{api-id}.execute-api.us-east-1.amazonaws.com
```

Luego actualiza el archivo `.env` con esa URL.

## 📝 Nota Importante

El servicio `airflow-assignment` debe desplegarse **después** de los otros servicios para que Airflow pueda usar el Lambda de asignación.

