# Serverless Compose - Despliegue de Servicios

## 📋 Configuración

Este proyecto usa `serverless-compose.yml` para gestionar y desplegar todos los servicios de una vez.

## 🚀 Despliegue

### Desplegar todos los servicios

Desde el directorio `Backend-Hackaton-CloudComputing`:

```bash
serverless deploy
```

Esto desplegará todos los servicios en el orden correcto según sus dependencias.

### Desplegar un servicio específico

```bash
serverless deploy --service seguridad-usuarios
serverless deploy --service incidentes
serverless deploy --service alerta-incidentes-api
serverless deploy --service alerta-utec-admin-panel
serverless deploy --service alerta-realtime
```

## 🔧 Variables de Entorno

Asegúrate de tener configuradas las variables de entorno:

```bash
# Crear archivo .env
cp env.template .env

# Editar .env con tus valores
AWS_ACCOUNT_ID=645337731455
SLS_ORG=darosv
STAGE=production
```

O exportarlas directamente:

```bash
export AWS_ACCOUNT_ID=645337731455
export SLS_ORG=darosv
export STAGE=production
```

## 📦 Orden de Despliegue

Los servicios se despliegan en este orden (según dependencias):

1. **seguridad-usuarios** - Crea tablas de usuarios y tokens
2. **incidentes** - Crea tabla de incidentes (depende de seguridad-usuarios)
3. **alerta-incidentes-api** - Usa tabla de incidentes (depende de incidentes)
4. **alerta-utec-admin-panel** - Usa tabla de incidentes (depende de incidentes)
5. **alerta-realtime** - Usa stream de incidentes (depende de incidentes)

## 📝 Estructura

```
Backend-Hackaton-CloudComputing/
├── serverless-compose.yml    # Configuración de todos los servicios
├── env.template              # Template de variables de entorno
├── seguridad-usuarios/
│   └── serverless.yml
├── Incidentes/
│   └── serverless.yml
├── alerta-incidentes-api/
│   └── serverless.yml
├── alerta-utec-admin-panel/
│   └── serverless.yml
└── alerta-realtime/
    └── serverless.yml
```

## 🔍 Comandos Útiles

```bash
# Ver estado de los servicios
serverless info

# Ver logs
serverless logs --service incidentes --function crearIncidente

# Eliminar todos los servicios
serverless remove
```

## 📚 Referencias

- [Serverless Framework Compose Documentation](https://www.serverless.com/framework/docs/guides/compose)
- [Multi-Service Deployments](https://www.serverless.com/blog/serverless-framework-compose-multi-service-deployments)

