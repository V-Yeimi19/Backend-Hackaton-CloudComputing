# 🚨 AlertaUTEC - Backend Serverless

**Backend serverless para la plataforma AlertaUTEC** - Sistema de gestión de reportes e incidentes del campus universitario con notificaciones en tiempo real.

Desarrollado para la Hackatón del curso de Cloud Computing - UTEC (Ciclo 2025-2)

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Arquitectura](#-arquitectura)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Flujo de Trabajo](#-flujo-de-trabajo)
- [Despliegue Rápido](#-despliegue-rápido)
- [Endpoints API](#-endpoints-api)
- [Tablas DynamoDB](#-tablas-dynamodb)
- [WebSocket en Tiempo Real](#-websocket-en-tiempo-real)
- [Troubleshooting](#-troubleshooting)
- [Ejemplos de Uso](#-ejemplos-de-uso)

---

## 🎯 Descripción

AlertaUTEC es una plataforma serverless que permite:

- ✅ **Reportar incidentes** en el campus universitario
- ✅ **Asignación automática** de trabajadores según categoría del incidente
- ✅ **Notificaciones en tiempo real** vía WebSocket
- ✅ **Gestión de estados** con validación mediante Apache Airflow
- ✅ **Autenticación** de usuarios y trabajadores
- ✅ **Historial completo** de todos los incidentes

### Características Principales

- **100% Serverless**: AWS Lambda + API Gateway + DynamoDB
- **Auto-asignación inteligente**: Categoría → Rol del trabajador
- **Tiempo real**: WebSocket + DynamoDB Streams
- **Validación de flujos**: Apache Airflow simulator
- **Escalable**: DynamoDB PAY_PER_REQUEST

---

## 🏗️ Arquitectura

### Diagrama de Microservicios

```
┌────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA SERVERLESS                      │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│  microservicio-     │     │   api-              │     │   alerta-realtime    │
│    reportes         │     │   authentication    │     │                      │
│                     │     │                     │     │                      │
│  📝 crearReporte    │     │  🔐 Autenticación   │     │  📡 WebSocket API    │
│  📄 obtenerReporte  │     │  👷 gestionTrabaj.  │     │  🔔 Broadcasting     │
│                     │     │  ✏️  actualizarInc. │     │  🤖 Auto-asignación  │
│                     │     │  📊 obtenerHistorial│     │                      │
│                     │     │  ⚙️  Airflow Sim.   │     │                      │
└──────────┬──────────┘     └──────────┬──────────┘     └──────────┬───────────┘
           │                           │                           │
           │ escribe                   │ lee/escribe               │ escucha Stream
           ▼                           ▼                           ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │              📦 DynamoDB: alerta-utec-Reporte-{stage}            │
    │                                                                   │
    │  Campos: id, UsuarioId, DescripcionCorta, Categoria, Gravedad,  │
    │          Lugar, Estado, TrabajadorId, FechaCreacion, etc.       │
    │                                                                   │
    │  🔄 DynamoDB Streams: ENABLED (NEW_AND_OLD_IMAGES)              │
    └──────────────────────────────────────────────────────────────────┘
                                       │
                                       │ Stream events
                                       ▼
                     ┌────────────────────────────────────┐
                     │   Lambda: dynamoStreamBroadcast    │
                     │                                    │
                     │  🔹 Broadcasting → WebSocket       │
                     │  🔹 Si INSERT → Auto-invoca        │
                     │     gestionTrabajadores            │
                     └────────────────────────────────────┘
```

### Flujo de Datos Completo

```
1️⃣  Usuario → POST /reportes
    ↓
2️⃣  Lambda crearReporte → DynamoDB (Estado: "Notificado")
    ↓
3️⃣  DynamoDB Stream → dynamoStreamBroadcast
    ├─→ 📡 Broadcasting WebSocket (clientes notificados)
    └─→ 🤖 Auto-invoca gestionTrabajadores
           ↓
4️⃣       Asigna trabajador por categoría
           ↓
5️⃣       Valida con Airflow: Notificado → En Proceso
           ↓
6️⃣       Actualiza DynamoDB (Estado: "En Proceso" + TrabajadorId)
           ↓
7️⃣  DynamoDB Stream → dynamoStreamBroadcast
    ↓
8️⃣  📡 Broadcasting WebSocket (clientes ven asignación)
```

---

## 📁 Estructura del Proyecto

```
Backend-Hackaton-CloudComputing/
│
├── 📂 microservicio-reportes/          # Gestión de reportes
│   ├── serverless.yml                  # Configuración del servicio
│   └── reporte/
│       ├── crearReporte.py            # Crear nuevo reporte
│       └── obtenerReporte.py          # Obtener reporte por ID
│
├── 📂 auth/                            # Autenticación y gestión
│   ├── serverless.yml                  # Configuración del servicio
│   ├── Lambda_CrearUsuario.py         # Registro de usuarios
│   ├── Lambda_LoginUsuario.py         # Inicio de sesión
│   ├── Lambda_ValidarToken.py         # Validación de tokens
│   ├── Lambda_GestionTrabajadores.py  # Asignación automática de trabajadores
│   ├── Lambda_ActualizarIncidente.py  # Actualización de estados
│   ├── Lambda_ObtenerHistorial.py     # Lista todos los incidentes
│   └── Lambda_AirflowSimulator.py     # Simulador de Airflow
│
├── 📂 alerta-realtime/                 # WebSocket y notificaciones
│   ├── serverless.yml                  # Configuración del servicio
│   ├── websocket_connect.py           # Manejo de conexiones WebSocket
│   ├── websocket_disconnect.py        # Manejo de desconexiones
│   └── dynamo_stream_broadcast.py     # Broadcasting + auto-asignación
│
├── 📜 deploy.sh                        # Script de despliegue automatizado
├── 📜 destroy.sh                       # Script de limpieza de recursos
└── 📘 README.md                        # Esta documentación
```

---

## 🔄 Flujo de Trabajo

### Estados del Incidente

```
Notificado → En Proceso → Finalizado
```

### Mapeo Categoría → Rol del Trabajador

| Categoría | Rol Asignado |
|-----------|-------------|
| **Fugas** | Técnico de Mantenimiento |
| **Calidad del Inmobiliario** | Técnico de Mantenimiento |
| **Limpieza y desorden** | Personal de Limpieza |
| **Calidad de los Servicios (Luz, Internet, Agua)** | OIT |
| **Aulas Cerradas** | Seguridad |
| **Objeto Perdido** | Seguridad |

### Proceso Completo

1. **Usuario crea reporte** → `POST /reportes`
   - Estado inicial: "Notificado"
   - Se almacena en DynamoDB

2. **DynamoDB Stream dispara lambda**
   - Broadcasting a clientes WebSocket
   - **Auto-asignación**: invoca `gestionTrabajadores`

3. **Asignación automática**
   - Mapea categoría → rol
   - Busca trabajador con `role="Trabajador"` y `area_trabajo="{rol}"`
   - Valida transición con Airflow
   - Actualiza estado a "En Proceso"

4. **Segundo broadcasting**
   - Clientes WebSocket reciben actualización con trabajador asignado

5. **Trabajador finaliza** → `PUT /incidente/actualizar`
   - Valida transición con Airflow
   - Actualiza estado a "Finalizado"

6. **Tercer broadcasting**
   - Clientes WebSocket reciben notificación de finalización

---

## 🚀 Despliegue Rápido

### Prerrequisitos

```bash
# 1. Node.js y npm
node --version  # v14 o superior
npm --version

# 2. Serverless Framework
npm install -g serverless

# 3. AWS CLI configurado
aws configure
```

Para **AWS Academy**, edita `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
aws_session_token = YOUR_SESSION_TOKEN
region = us-east-1
```

⚠️ **Las credenciales de AWS Academy expiran**. Actualízalas cada sesión del Learner Lab.

### Despliegue Automatizado

```bash
# Clonar el repositorio
cd Backend-Hackaton-CloudComputing

# Dar permisos de ejecución
chmod +x deploy.sh destroy.sh

# Desplegar TODO en stage 'dev'
./deploy.sh dev

# O en stage 'prod'
./deploy.sh prod
```

**Tiempo estimado**: 5-10 minutos

El script desplegará automáticamente los 3 microservicios en el orden correcto:
1. ✅ `microservicio-reportes` (crea tabla con Streams)
2. ✅ `auth` (crea lambdas y tablas de usuarios)
3. ✅ `alerta-realtime` (configura WebSocket y listeners)

### Despliegue Manual

Si prefieres desplegar paso a paso:

```bash
# 1. microservicio-reportes
cd microservicio-reportes
serverless deploy --stage dev
cd ..

# 2. auth
cd auth
serverless deploy --stage dev
cd ..

# 3. alerta-realtime
cd alerta-realtime
serverless deploy --stage dev
cd ..
```

### Verificar Despliegue

```bash
# Ver información de cada servicio
cd microservicio-reportes
serverless info --stage dev

cd ../auth
serverless info --stage dev

cd ../alerta-realtime
serverless info --stage dev
```

### Ver Logs en Tiempo Real

```bash
# Logs de una función específica
serverless logs -f crearReporte --tail --stage dev
serverless logs -f gestionTrabajadores --tail --stage dev
serverless logs -f dynamoStreamBroadcast --tail --stage dev
```

---

## 🌐 Endpoints API

### microservicio-reportes

**Base URL**: `https://[API-ID].execute-api.us-east-1.amazonaws.com/dev`

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/reportes` | Crear un nuevo reporte |
| `GET` | `/reportes/{id}` | Obtener un reporte específico |

### auth (api-authentication)

**Base URL**: `https://[API-ID].execute-api.us-east-1.amazonaws.com/dev`

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/usuario/register` | Registrar nuevo usuario/trabajador |
| `POST` | `/usuario/login` | Iniciar sesión |
| `POST` | `/usuario/validate-token` | Validar token de sesión |
| `POST` | `/incidente/asignar` | Asignar trabajador manualmente (opcional) |
| `PUT` | `/incidente/actualizar` | Actualizar estado del incidente |
| `GET` | `/incidente/historial` | Obtener historial completo de incidentes |
| `POST` | `/airflow/validar-cambio-estado` | Validar transición de estado |
| `POST` | `/airflow/ejecutar-workflow` | Ejecutar workflow de Airflow |

---

## 🗄️ Tablas DynamoDB

### 1. `alerta-utec-Reporte-{stage}`

Tabla principal de reportes/incidentes (creada por microservicio-reportes).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| **`id`** | String (PK) | UUID único del reporte |
| `UsuarioId` | String | ID del usuario que creó el reporte |
| `DescripcionCorta` | String | Descripción breve del incidente |
| `Categoria` | String | Categoría del incidente (6 opciones) |
| `Gravedad` | String | `debil`, `moderado`, `fuerte` |
| `Lugar` | String | Ubicación del incidente |
| `Estado` | String | `Notificado`, `En Proceso`, `Finalizado` |
| `TrabajadorId` | String | ID del trabajador asignado (opcional) |
| `FechaCreacion` | String | Timestamp ISO de creación |
| `FechaActualizacion` | String | Timestamp ISO de última actualización |
| `FechaResolucion` | String | Timestamp ISO de resolución (opcional) |
| `ResueltoPor` | String | Nombre del trabajador que resolvió (opcional) |

**Streams**: ✅ Habilitado (`NEW_AND_OLD_IMAGES`)

### 2. `alerta-utec-AsignacionResponsables-{stage}`

Tabla de asignaciones de responsables (creada por microservicio-reportes).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| **`ReporteId`** | String (PK) | ID del reporte |
| `TrabajadoresId` | List | Lista de IDs de trabajadores asignados |

### 3. `{stage}-t_usuarios_hack`

Tabla de usuarios y trabajadores (creada por auth).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| **`correo`** | String (PK) | Email del usuario |
| `password` | String | Contraseña hasheada |
| `nombre` | String | Nombre completo |
| `role` | String | `Usuario`, `Trabajador`, `Admin` |
| `area_trabajo` | String | Área del trabajador (si aplica) |

### 4. `{stage}-t_tokens_acceso`

Tabla de tokens de sesión (creada por auth).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| **`token`** | String (PK) | Token JWT |
| `correo` | String | Email del usuario |
| `expiracion` | Number | Timestamp de expiración |

### 5. `alerta-utec-connections-{stage}`

Tabla de conexiones WebSocket activas (creada por alerta-realtime).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| **`connectionId`** | String (PK) | ID de la conexión WebSocket |
| `connectedAt` | String | Timestamp de conexión |

---

## 📡 WebSocket en Tiempo Real

### Conectar al WebSocket

**URL**: `wss://[WEBSOCKET-ID].execute-api.us-east-1.amazonaws.com/dev`

```javascript
const ws = new WebSocket('wss://[WEBSOCKET-ID].execute-api.us-east-1.amazonaws.com/dev');

ws.onopen = () => {
  console.log('✅ Conectado al WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('📨 Evento recibido:', data);

  // Estructura del mensaje:
  // {
  //   "eventName": "INSERT" | "MODIFY" | "REMOVE",
  //   "newImage": { ...datos del reporte... },
  //   "oldImage": { ...datos anteriores (si aplica)... }
  // }

  if (data.eventName === 'INSERT') {
    console.log('🆕 Nuevo reporte creado:', data.newImage);
  } else if (data.eventName === 'MODIFY') {
    console.log('✏️ Reporte actualizado:', data.newImage);
    console.log('📝 Datos anteriores:', data.oldImage);
  }
};

ws.onerror = (error) => {
  console.error('❌ Error WebSocket:', error);
};

ws.onclose = () => {
  console.log('🔌 Desconectado del WebSocket');
};
```

### Tipos de Eventos

| Evento | Cuándo se dispara | Datos incluidos |
|--------|-------------------|-----------------|
| `INSERT` | Nuevo reporte creado | `newImage` con datos completos |
| `MODIFY` | Reporte actualizado (asignación, estado) | `newImage` + `oldImage` |
| `REMOVE` | Reporte eliminado | `oldImage` con datos eliminados |

---

## 🔍 Troubleshooting

### Error: "Serverless command not found"

```bash
npm install -g serverless
```

### Error: "Access Denied" o "Credentials not valid"

Las credenciales de AWS Academy expiraron. Actualiza `~/.aws/credentials` con nuevas credenciales del Learner Lab.

### Error: "Stack does not exist"

Primera vez desplegando. Esto es normal. El stack se creará automáticamente.

### Error: "ResourceNotFoundException: Requested resource not found"

Asegúrate de desplegar en el orden correcto:
1. Primero `microservicio-reportes` (crea la tabla)
2. Luego `auth` y `alerta-realtime`

O usa el script automatizado:
```bash
./deploy.sh dev
```

### Error: "No trabajador disponible con rol X"

Necesitas crear trabajadores primero usando el endpoint de registro:

```bash
curl -X POST https://[API-URL]/dev/usuario/register \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "tecnico1@utec.edu.pe",
    "password": "password123",
    "nombre": "Juan Pérez",
    "role": "Trabajador",
    "area_trabajo": "Tecnico de Mantenimiento"
  }'
```

### WebSocket no se conecta

Verifica que `alerta-realtime` se desplegó correctamente:

```bash
cd alerta-realtime
serverless info --stage dev
```

Busca la URL del WebSocket en el output y úsala en tu cliente.

### Ver logs de errores

```bash
cd [directorio-del-servicio]
serverless logs -f [nombre-funcion] --tail --stage dev

# Ejemplos:
serverless logs -f crearReporte --tail --stage dev
serverless logs -f gestionTrabajadores --tail --stage dev
serverless logs -f dynamoStreamBroadcast --tail --stage dev
```

---

## 💡 Ejemplos de Uso

### 1. Crear un Trabajador

```bash
curl -X POST https://[API-URL]/dev/usuario/register \
  -H "Content-Type: application/json" \
  -d '{
    "correo": "limpieza1@utec.edu.pe",
    "password": "password123",
    "nombre": "María López",
    "role": "Trabajador",
    "area_trabajo": "Personal de Limpieza"
  }'
```

**Trabajadores necesarios** (mínimo uno de cada):
- `area_trabajo: "Tecnico de Mantenimiento"`
- `area_trabajo: "Personal de Limpieza"`
- `area_trabajo: "OIT"`
- `area_trabajo: "Seguridad"`

### 2. Crear un Reporte (Dispara el flujo completo)

```bash
curl -X POST https://[API-URL]/dev/reportes \
  -H "Content-Type: application/json" \
  -d '{
    "UsuarioId": "user123",
    "DescripcionCorta": "Fuga de agua en el baño del segundo piso",
    "Categoria": "Fugas",
    "Gravedad": "moderado",
    "Lugar": "Pabellón A - Baño 2do piso"
  }'
```

**¿Qué sucede automáticamente?**
1. ✅ Se crea el reporte (Estado: "Notificado")
2. ✅ DynamoDB Stream dispara `dynamoStreamBroadcast`
3. ✅ Broadcasting a clientes WebSocket
4. ✅ **Auto-asignación**: Se invoca `gestionTrabajadores`
5. ✅ Se busca trabajador con `area_trabajo="Tecnico de Mantenimiento"`
6. ✅ Se valida con Airflow: Notificado → En Proceso
7. ✅ Se actualiza el reporte (Estado: "En Proceso" + TrabajadorId)
8. ✅ Segundo broadcasting con trabajador asignado

### 3. Obtener Historial de Incidentes

```bash
curl https://[API-URL]/dev/incidente/historial
```

**Respuesta** ejemplo:
```json
{
  "total": 25,
  "incidentes": [
    {
      "id": "uuid-123",
      "UsuarioId": "user123",
      "DescripcionCorta": "Fuga de agua en el baño",
      "Categoria": "Fugas",
      "Gravedad": "moderado",
      "Lugar": "Pabellón A - Baño 2do piso",
      "Estado": "En Proceso",
      "TrabajadorId": "tecnico1@utec.edu.pe",
      "FechaCreacion": "2025-11-16T10:30:00",
      "FechaActualizacion": "2025-11-16T10:30:05"
    },
    ...
  ]
}
```

### 4. Actualizar Estado de Incidente (Finalizar)

```bash
curl -X PUT https://[API-URL]/dev/incidente/actualizar \
  -H "Content-Type: application/json" \
  -d '{
    "id": "uuid-123",
    "status": "Finalizado",
    "resolvedBy": "Juan Pérez"
  }'
```

**Validación Airflow**:
- ✅ Verifica transición válida: En Proceso → Finalizado
- ✅ Ejecuta workflow simulado
- ✅ Actualiza DynamoDB
- ✅ Broadcasting a WebSocket

### 5. Conectar Cliente WebSocket (Frontend)

```html
<!DOCTYPE html>
<html>
<head>
  <title>AlertaUTEC - Notificaciones en Tiempo Real</title>
</head>
<body>
  <h1>Notificaciones en Tiempo Real</h1>
  <div id="notifications"></div>

  <script>
    const ws = new WebSocket('wss://[WEBSOCKET-ID].execute-api.us-east-1.amazonaws.com/dev');

    ws.onopen = () => {
      console.log('✅ Conectado');
      document.getElementById('notifications').innerHTML += '<p>✅ Conectado al servidor</p>';
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const notif = document.createElement('div');

      if (data.eventName === 'INSERT') {
        notif.innerHTML = `🆕 Nuevo reporte: ${data.newImage.DescripcionCorta} (${data.newImage.Categoria})`;
      } else if (data.eventName === 'MODIFY') {
        notif.innerHTML = `✏️ Actualización: ${data.newImage.DescripcionCorta} - Estado: ${data.newImage.Estado}`;
      }

      document.getElementById('notifications').appendChild(notif);
    };
  </script>
</body>
</html>
```

---

## 🗑️ Limpieza de Recursos

**ADVERTENCIA**: Esto eliminará TODOS los recursos. Esta acción es **IRREVERSIBLE**.

```bash
# Eliminar todos los recursos del stage 'dev'
./destroy.sh dev

# El script pedirá confirmación. Escribe 'SI' para continuar.
```

Esto es útil cuando:
- ✅ Terminas tu sesión de AWS Academy
- ✅ Quieres limpiar recursos para evitar costos
- ✅ Necesitas un despliegue completamente limpio

---

## ⚙️ Configuración Avanzada

### Actualizar URLs de Airflow

Después del despliegue, actualiza las URLs reales en `auth/serverless.yml`:

```yaml
custom:
  apiGatewayUrl:
    dev: https://[TU-API-ID].execute-api.us-east-1.amazonaws.com/dev
    test: https://[TU-API-ID].execute-api.us-east-1.amazonaws.com/test
    prod: https://[TU-API-ID].execute-api.us-east-1.amazonaws.com/prod
```

Obtén la URL ejecutando:
```bash
cd auth
serverless info --stage dev
```

Luego redespliega:
```bash
serverless deploy --stage dev
```

### Cambiar Stage

Puedes desplegar en diferentes stages (dev, test, prod):

```bash
./deploy.sh dev    # Desarrollo
./deploy.sh test   # Pruebas
./deploy.sh prod   # Producción
```

Cada stage crea recursos independientes con nombres diferentes:
- `alerta-utec-Reporte-dev`
- `alerta-utec-Reporte-test`
- `alerta-utec-Reporte-prod`

---

## 📊 Tecnologías Utilizadas

- **AWS Lambda** - Ejecución de código serverless
- **API Gateway** - REST APIs y WebSocket APIs
- **DynamoDB** - Base de datos NoSQL
- **DynamoDB Streams** - Captura de cambios en tiempo real
- **Serverless Framework** - Despliegue y gestión de infraestructura
- **Python 3.12/3.13** - Runtime de las funciones Lambda
- **Apache Airflow (Simulator)** - Validación de flujos de trabajo

---

## 👥 Autores

Equipo AlertaUTEC - UTEC (2025-2)
- Yeimi Varela
- Jhogan Pachacutec

---

## 📝 Licencia

Este proyecto fue desarrollado como parte de la Hackatón del curso de Cloud Computing en UTEC.

---

## ✅ Checklist de Despliegue

- [ ] Node.js y npm instalados
- [ ] Serverless Framework instalado (`npm install -g serverless`)
- [ ] AWS CLI configurado con credenciales de AWS Academy
- [ ] Credenciales actualizadas (no expiradas)
- [ ] Script `deploy.sh` tiene permisos de ejecución (`chmod +x deploy.sh`)
- [ ] Ejecutar `./deploy.sh dev`
- [ ] Verificar que los 3 servicios se desplegaron correctamente
- [ ] Crear al menos un trabajador de cada tipo
- [ ] Probar creación de reporte y verificar auto-asignación
- [ ] Conectar cliente WebSocket y verificar notificaciones

---

**¡Listo para desplegar! 🚀**

```bash
./deploy.sh dev
```

---

## 🔗 Enlaces Útiles

- [Documentación de Serverless Framework](https://www.serverless.com/framework/docs)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html)
- [API Gateway WebSocket APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html)
