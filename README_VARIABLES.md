# Configuración de Variables - AlertaUTEC Backend

## 📋 Variables Encapsuladas

Solo se han encapsulado las siguientes 3 variables esenciales:

1. **AWS_ACCOUNT_ID** - ID de cuenta de AWS (645337731455)
2. **SLS_ORG** - Organización de Serverless Framework (darosv)
3. **STAGE** - Stage de despliegue (dev, test, prod)

## 🔧 Configuración

### 1. Crear archivo .env

Copia el template y configura tus valores:

```bash
cp env.template .env
```

Edita `.env`:

```env
# AWS Account ID
AWS_ACCOUNT_ID=645337731455

# Serverless Framework Organization
SLS_ORG=darosv

# Stage: dev, test, o prod
STAGE=production
```

### 2. Desplegar

**Linux/Mac:**
```bash
chmod +x deploy-all.sh
./deploy-all.sh production
# o para otro stage:
./deploy-all.sh dev
```

**Windows:**
```powershell
.\deploy-all.ps1 production
# o para otro stage:
.\deploy-all.ps1 dev
```

## 📦 Archivos Modificados

Todos los `serverless.yml` ahora usan variables de entorno:

- `Incidentes/serverless.yml`
- `alerta-incidentes-api/serverless.yml`
- `alerta-utec-admin-panel/serverless.yml`
- `seguridad-usuarios/serverless.yml`
- `alerta-realtime/serverless.yml`

### Cambios Aplicados

1. **Account ID**: `arn:aws:iam::645337731455:role/LabRole` → `arn:aws:iam::${self:custom.awsAccountId}:role/LabRole`
2. **Org**: `org: darosv` → `org: ${self:custom.org}`
3. **Stage**: `stage: production` → `stage: ${self:custom.stage}`
4. **Stream ARN**: También actualizado para usar `${self:custom.awsAccountId}`

## ✅ Verificación

No se encontraron referencias hardcodeadas en código Python. Todos los valores están solo en los archivos `serverless.yml` y ahora usan variables de entorno.

## 🎯 Uso por Stage

### Desarrollo
```bash
export STAGE=dev
./deploy-all.sh dev
```

### Testing
```bash
export STAGE=test
./deploy-all.sh test
```

### Producción
```bash
export STAGE=production
./deploy-all.sh production
```

## 📝 Notas

- El archivo `serverless.common.yml` contiene solo las 3 variables esenciales
- Cada servicio carga esta configuración común
- Los valores por defecto están en `serverless.common.yml` si no se define `.env`
- El archivo `.env` NO debe committearse (agregar a `.gitignore`)

