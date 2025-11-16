# 🚀 Guía de Despliegue - Backend Alerta UTEC

## 📋 Prerrequisitos

### 1. **Node.js y npm**
```bash
# Verificar instalación
node --version  # Debe ser v14 o superior
npm --version
```

### 2. **Serverless Framework**
```bash
# Instalar globalmente
npm install -g serverless

# Verificar instalación
serverless --version
```

### 3. **AWS CLI configurado**
```bash
# Instalar AWS CLI (si no está instalado)
pip install awscli

# Configurar credenciales de AWS Academy
aws configure
```

Para AWS Academy, necesitarás:
- **AWS Access Key ID**: Obtén de AWS Academy Learner Lab
- **AWS Secret Access Key**: Obtén de AWS Academy Learner Lab
- **AWS Session Token**: Obtén de AWS Academy Learner Lab
- **Region**: `us-east-1`

#### Configuración de credenciales para AWS Academy:

Edita `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
aws_session_token = YOUR_SESSION_TOKEN
```

**IMPORTANTE**: Las credenciales de AWS Academy expiran. Actualízalas cada vez que inicies una nueva sesión del Learner Lab.

---

## 🔧 Configuración Inicial

### 1. Clonar el repositorio
```bash
cd /home/yiyi/Escritorio/Yeimi/UTEC/4to\ ciclo/Cloud\ Computing/hackaton/
cd Backend-Hackaton-CloudComputing
```

### 2. Verificar estructura del proyecto
```
Backend-Hackaton-CloudComputing/
├── microservicio-reportes/
│   ├── serverless.yml
│   └── reportes/
├── auth/
│   ├── serverless.yml
│   └── Lambda_*.py
├── alerta-realtime/
│   ├── serverless.yml
│   ├── websocket_connect.py
│   ├── websocket_disconnect.py
│   └── dynamo_stream_broadcast.py
├── deploy.sh          # Script de despliegue
├── destroy.sh         # Script de eliminación
└── DEPLOYMENT.md      # Este archivo
```

---

## 🚀 Despliegue Automatizado

### Opción 1: Despliegue completo con un comando

```bash
# Desplegar en stage 'dev' (recomendado)
./deploy.sh dev

# O desplegar en stage 'prod'
./deploy.sh prod
```

El script ejecutará automáticamente:
1. ✅ Despliega `microservicio-reportes` (crea tabla con Streams)
2. ✅ Despliega `auth` (crea lambdas y tablas de usuarios)
3. ✅ Despliega `alerta-realtime` (configura WebSocket y listeners)

**Tiempo estimado**: 5-10 minutos

### Opción 2: Despliegue manual (paso a paso)

Si prefieres desplegar manualmente:

```bash
# 1. Desplegar microservicio-reportes
cd microservicio-reportes
serverless deploy --stage dev --verbose
cd ..

# 2. Desplegar auth
cd auth
serverless deploy --stage dev --verbose
cd ..

# 3. Desplegar alerta-realtime
cd alerta-realtime
serverless deploy --stage production --verbose
cd ..
```

---

## 📊 Verificar Despliegue

### Ver información de los servicios desplegados

```bash
# Información de microservicio-reportes
cd microservicio-reportes
serverless info --stage dev

# Información de auth
cd ../auth
serverless info --stage dev

# Información de alerta-realtime
cd ../alerta-realtime
serverless info --stage production
```

### Ver logs en tiempo real

```bash
# Logs de una función específica
serverless logs -f crearReporte --tail --stage dev

# Ejemplos de otras funciones
serverless logs -f gestionTrabajadores --tail --stage dev
serverless logs -f dynamoStreamBroadcast --tail --stage production
```

---

## 🧪 Probar el Sistema

### 1. Crear un trabajador (usando Postman o curl)

```bash
# Endpoint: POST /usuario/register
# URL: Obtener de 'serverless info' en auth

curl -X POST https://[API-GATEWAY-URL]/dev/usuario/register \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "tecnico1@utec.edu.pe",
    "password": "password123",
    "nombre": "Juan Pérez",
    "role": "Trabajador",
    "area_trabajo": "Tecnico de Mantenimiento"
  }'
```

### 2. Crear un reporte (dispara el flujo automático)

```bash
# Endpoint: POST /reportes
# URL: Obtener de 'serverless info' en microservicio-reportes

curl -X POST https://[API-GATEWAY-URL]/dev/reportes \
  -H "Content-Type: application/json" \
  -d '{
    "UsuarioId": "user123",
    "DescripcionCorta": "Fuga de agua en el baño",
    "Categoria": "Fugas",
    "Gravedad": "moderado",
    "Lugar": "Pabellón A - Baño 2do piso"
  }'
```

**¿Qué sucede automáticamente?**
1. ✅ Se crea el reporte en DynamoDB (Estado: "Notificado")
2. ✅ DynamoDB Stream dispara `dynamoStreamBroadcast`
3. ✅ Broadcasting a clientes WebSocket
4. ✅ **Auto-asignación**: Se invoca `gestionTrabajadores` automáticamente
5. ✅ Se asigna un trabajador con el área correcta (Estado: "En Proceso")
6. ✅ Segundo broadcasting con el trabajador asignado

### 3. Conectar cliente WebSocket

```javascript
// En tu frontend o cliente WebSocket
const ws = new WebSocket('wss://[WEBSOCKET-URL]/production');

ws.onopen = () => {
  console.log('Conectado al WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Evento recibido:', data);

  // data.eventName puede ser: "INSERT", "MODIFY", "REMOVE"
  // data.newImage: Datos actualizados del reporte
  // data.oldImage: Datos anteriores (si aplica)
};
```

### 4. Obtener historial de incidentes

```bash
# Endpoint: GET /incidente/historial
curl https://[API-GATEWAY-URL]/dev/incidente/historial
```

---

## 🗑️ Eliminar Recursos (Limpiar AWS)

**ADVERTENCIA**: Esto eliminará TODOS los recursos. Esta acción es IRREVERSIBLE.

```bash
# Eliminar todos los recursos del stage 'dev'
./destroy.sh dev

# El script pedirá confirmación. Escribe 'SI' para continuar.
```

Esto es útil cuando:
- Terminas tu sesión de AWS Academy
- Quieres limpiar recursos para evitar costos
- Necesitas hacer un despliegue completamente limpio

---

## 🔍 Troubleshooting

### Error: "Serverless command not found"

```bash
npm install -g serverless
```

### Error: "Access Denied" o "Credentials not valid"

Las credenciales de AWS Academy expiraron. Actualiza `~/.aws/credentials` con nuevas credenciales del Learner Lab.

### Error: "Stack does not exist"

Si es tu primer despliegue, esto es normal. El stack se creará automáticamente.

### Error: "Resource already exists"

Si ya desplegaste antes, elimina primero con `./destroy.sh` y vuelve a desplegar.

### Ver logs de errores

```bash
# Logs de una función específica con errores
cd [directorio-del-servicio]
serverless logs -f [nombre-funcion] --tail --stage dev

# Ejemplo:
cd auth
serverless logs -f gestionTrabajadores --tail --stage dev
```

### Tabla no encontrada

Asegúrate de desplegar en el orden correcto:
1. Primero `microservicio-reportes` (crea la tabla)
2. Luego `auth` y `alerta-realtime`

### WebSocket no funciona

Verifica que `alerta-realtime` se desplegó correctamente:
```bash
cd alerta-realtime
serverless info --stage production
```

Busca la URL del WebSocket en el output.

---

## 📝 Configuración Adicional

### Actualizar URLs de Airflow

Después del despliegue, actualiza las URLs de Airflow en `auth/serverless.yml`:

```yaml
custom:
  apiGatewayUrl:
    dev: https://[TU-API-GATEWAY-ID].execute-api.us-east-1.amazonaws.com/dev
    test: https://[TU-API-GATEWAY-ID].execute-api.us-east-1.amazonaws.com/test
    prod: https://[TU-API-GATEWAY-ID].execute-api.us-east-1.amazonaws.com/prod
```

Obtén la URL real ejecutando:
```bash
cd auth
serverless info --stage dev
```

Luego vuelve a desplegar:
```bash
serverless deploy --stage dev
```

---

## 📚 Arquitectura del Sistema

### Flujo de Datos

```
Usuario crea reporte
    ↓
microservicio-reportes/crearReporte
    ↓
DynamoDB: alerta-utec-Reporte-{stage}
    ↓
DynamoDB Stream dispara
    ↓
alerta-realtime/dynamoStreamBroadcast
    ├─→ Broadcasting WebSocket (notificación inmediata)
    └─→ Auto-invoca auth/gestionTrabajadores
            ↓
        Asigna trabajador automáticamente
            ↓
        Actualiza DynamoDB (Estado: "En Proceso")
            ↓
        DynamoDB Stream dispara
            ↓
        Broadcasting WebSocket (actualización)
```

### Tablas DynamoDB Creadas

| Tabla | Servicio | Descripción |
|-------|----------|-------------|
| `alerta-utec-Reporte-{stage}` | microservicio-reportes | Tabla principal de reportes/incidentes |
| `alerta-utec-AsignacionResponsables-{stage}` | microservicio-reportes | Asignación de responsables |
| `{stage}-t_usuarios_hack` | auth | Usuarios y trabajadores |
| `{stage}-t_tokens_acceso` | auth | Tokens de sesión |
| `alerta-utec-connections-production` | alerta-realtime | Conexiones WebSocket activas |

---

## ⚙️ Variables de Entorno

### microservicio-reportes
- `REPORTES_TABLE`: `alerta-utec-Reporte-${stage}`
- `ASIGNACIONES_TABLE`: `alerta-utec-AsignacionResponsables-${stage}`

### auth
- `TABLE_USUARIOS`: `${stage}-t_usuarios_hack`
- `TABLE_TOKENS`: `${stage}-t_tokens_acceso`
- `REPORTES_TABLE`: `alerta-utec-Reporte-${stage}`
- `AIRFLOW_API_URL`: URL del API Gateway
- `LAMBDA_GESTION_TRABAJADORES`: Nombre de la lambda

### alerta-realtime
- `CONNECTIONS_TABLE`: `alerta-utec-connections-${stage}`
- `WS_ENDPOINT`: URL del WebSocket API
- `LAMBDA_GESTION_TRABAJADORES`: `api-authentication-${stage}-gestionTrabajadores`

---

## 🎯 Próximos Pasos

1. ✅ Desplegar el backend con `./deploy.sh dev`
2. ✅ Crear trabajadores usando el endpoint de registro
3. ✅ Probar creación de reportes
4. ✅ Verificar auto-asignación de trabajadores
5. ✅ Conectar frontend al WebSocket para notificaciones en tiempo real

---

## 📞 Soporte

Si tienes problemas durante el despliegue:

1. Verifica los logs con `serverless logs -f [funcion] --tail`
2. Revisa la consola de AWS CloudWatch
3. Asegúrate de que las credenciales de AWS Academy estén actualizadas
4. Verifica que todos los archivos `serverless.yml` están correctamente configurados

---

## ✅ Checklist de Despliegue

- [ ] Node.js y npm instalados
- [ ] Serverless Framework instalado globalmente
- [ ] AWS CLI configurado con credenciales de AWS Academy
- [ ] Credenciales actualizadas (no expiradas)
- [ ] Script `deploy.sh` tiene permisos de ejecución (`chmod +x deploy.sh`)
- [ ] Ejecutar `./deploy.sh dev`
- [ ] Verificar que todos los servicios se desplegaron correctamente
- [ ] Probar endpoints con Postman o curl
- [ ] Conectar cliente WebSocket
- [ ] Crear al menos un trabajador de prueba
- [ ] Crear un reporte y verificar auto-asignación

---

**¡Listo para desplegar! 🚀**

```bash
./deploy.sh dev
```
