# 🎼 Guía de Serverless Compose - AlertaUTEC

## ¿Qué es Serverless Compose?

**Serverless Compose** es una herramienta del Serverless Framework que permite gestionar y desplegar múltiples servicios serverless de manera coordinada desde un solo punto.

## 🎯 Ventajas de Usar Serverless Compose

✅ **Despliegue Coordinado** - Despliega todos los servicios con un solo comando  
✅ **Gestión de Dependencias** - Asegura el orden correcto de despliegue  
✅ **Configuración Centralizada** - Un solo archivo para gestionar todos los servicios  
✅ **Paralelización** - Puede desplegar servicios independientes en paralelo  
✅ **Consistencia** - Mismo stage y región para todos los servicios  

## 📁 Estructura del Proyecto

```
Backend-Hackaton-CloudComputing/
├── serverless-compose.yml          # ← Configuración de Compose
├── microservicio-reportes/
│   ├── serverless.yml
│   ├── requirements.txt
│   └── reportes/
│       └── [funciones Lambda]
└── microservicio-analitica/
    ├── serverless.yml
    ├── requirements.txt
    ├── analitica/
    │   └── [funciones Lambda]
    └── ingesta/
        └── [funciones Lambda]
```

## 🚀 Uso de Serverless Compose

### Instalación

Serverless Compose viene incluido con Serverless Framework v3+. Verifica tu versión:

```bash
serverless --version
```

Si necesitas actualizar:

```bash
npm install -g serverless@latest
```

### Comandos Principales

#### 1. Desplegar Todos los Servicios

```bash
# Desde la raíz del proyecto
serverless deploy

# Con stage específico
serverless deploy --stage prod
```

**Orden de despliegue automático:**
1. Primero: `reportes` (crea tablas DynamoDB)
2. Segundo: `analitica` (usa tablas existentes)

#### 2. Desplegar un Servicio Específico

```bash
# Solo reportes
serverless deploy --service reportes

# Solo analítica
serverless deploy --service analitica
```

#### 3. Ver Información de los Servicios

```bash
# Información de todos los servicios
serverless info

# Información de un servicio específico
serverless info --service reportes
```

#### 4. Ver Logs

```bash
# Logs de todos los servicios
serverless logs --tail

# Logs de un servicio específico
serverless logs --service reportes --tail

# Logs de una función específica
serverless logs --service reportes --function crearReporte --tail
```

#### 5. Eliminar Todo

```bash
# Elimina todos los servicios (en orden inverso)
serverless remove

# Eliminar un servicio específico
serverless remove --service analitica
```

## 📋 Configuración del serverless-compose.yml

```yaml
services:
  reportes:
    path: microservicio-reportes
    params:
      stage: ${opt:stage, 'dev'}
      region: us-east-1

  analitica:
    path: microservicio-analitica
    params:
      stage: ${opt:stage, 'dev'}
      region: us-east-1
    dependsOn:
      - reportes  # ← Dependencia: se despliega después
```

### Explicación de la Configuración

- **`path`**: Ruta relativa al directorio del servicio
- **`params`**: Parámetros que se pasan a cada servicio
- **`dependsOn`**: Define dependencias entre servicios
  - `analitica` espera a que `reportes` termine antes de desplegarse

## 🔄 Flujo de Despliegue

Cuando ejecutas `serverless deploy`:

```
1. Serverless Compose lee serverless-compose.yml
2. Identifica dependencias (analitica depende de reportes)
3. Despliega reportes primero
   ├─ Crea tablas DynamoDB
   ├─ Crea funciones Lambda
   └─ Crea API Gateway
4. Espera a que reportes termine exitosamente
5. Despliega analitica
   ├─ Usa tablas DynamoDB existentes
   ├─ Crea funciones Lambda
   ├─ Crea recursos S3/Glue/Athena
   └─ Crea API Gateway
6. Muestra URLs de ambos servicios
```

## 📊 Comparación: Con vs Sin Compose

### Sin Serverless Compose

```bash
# Tienes que hacerlo manualmente
cd microservicio-reportes
serverless deploy
cd ../microservicio-analitica
serverless deploy
```

**Problemas:**
- ❌ Múltiples comandos
- ❌ Fácil olvidar el orden
- ❌ No hay gestión centralizada
- ❌ Difícil mantener consistencia

### Con Serverless Compose

```bash
# Un solo comando desde la raíz
serverless deploy
```

**Ventajas:**
- ✅ Un solo comando
- ✅ Orden automático según dependencias
- ✅ Gestión centralizada
- ✅ Consistencia garantizada

## 🎯 Casos de Uso

### Desarrollo Local

```bash
# Desplegar todo en dev
serverless deploy --stage dev
```

### Staging

```bash
# Desplegar todo en staging
serverless deploy --stage staging
```

### Producción

```bash
# Desplegar todo en producción
serverless deploy --stage prod
```

### Actualizar Solo un Servicio

```bash
# Solo actualizar reportes
serverless deploy --service reportes

# Solo actualizar analítica
serverless deploy --service analitica
```

## 🔍 Verificación Post-Despliegue

Después de `serverless deploy`, verás algo como:

```
Deploying "reportes" to stage "dev"...
Deploying "analitica" to stage "dev"...

Service Information
service: alerta-utec-reportes
stage: dev
region: us-east-1
endpoints:
  POST - https://xxx.execute-api.us-east-1.amazonaws.com/dev/reportes
  GET - https://xxx.execute-api.us-east-1.amazonaws.com/dev/reportes
  ...

Service Information
service: alerta-utec-analitica
stage: dev
region: us-east-1
endpoints:
  GET - https://yyy.execute-api.us-east-1.amazonaws.com/dev/analitica/reportes-activos
  ...
```

## ⚙️ Configuración Avanzada

### Variables Compartidas

Puedes definir variables compartidas en `serverless-compose.yml`:

```yaml
services:
  reportes:
    path: microservicio-reportes
    params:
      stage: ${opt:stage, 'dev'}
      sharedTableName: alerta-utec-Reporte-${opt:stage, 'dev'}

  analitica:
    path: microservicio-analitica
    params:
      stage: ${opt:stage, 'dev'}
      sharedTableName: alerta-utec-Reporte-${opt:stage, 'dev'}
    dependsOn:
      - reportes
```

### Despliegue en Paralelo

Si tienes servicios sin dependencias, Compose los despliega en paralelo automáticamente.

### Hooks Personalizados

Puedes agregar hooks antes/después del despliegue:

```yaml
services:
  reportes:
    path: microservicio-reportes
    hooks:
      before:deploy:
        - echo "Desplegando reportes..."
      after:deploy:
        - echo "Reportes desplegado exitosamente"
```

## 🐛 Troubleshooting

### Error: "Service not found"

Verifica que las rutas en `serverless-compose.yml` sean correctas:
```yaml
path: microservicio-reportes  # ← Debe existir esta carpeta
```

### Error: "Dependency failed"

Si `analitica` falla porque `reportes` no está desplegado:
1. Verifica que `reportes` se desplegó correctamente
2. Verifica que las tablas DynamoDB existen
3. Revisa los logs: `serverless logs --service reportes`

### Error: "Table already exists"

Si las tablas ya existen de un despliegue anterior:
- Opción 1: Eliminar todo y empezar de nuevo: `serverless remove`
- Opción 2: Las tablas se reutilizan automáticamente (no hay problema)

## 📝 Checklist de Uso

- [ ] Serverless Framework v3+ instalado
- [ ] `serverless-compose.yml` creado en la raíz
- [ ] Ambos `serverless.yml` configurados correctamente
- [ ] Dependencias instaladas en ambos servicios
- [ ] `serverless deploy` ejecutado exitosamente
- [ ] URLs de ambos servicios copiadas
- [ ] Postman configurado con ambas URLs

## 🎓 Recursos Adicionales

- [Documentación Oficial de Serverless Compose](https://www.serverless.com/framework/docs/guides/compose)
- [Serverless Framework Docs](https://www.serverless.com/framework/docs)

