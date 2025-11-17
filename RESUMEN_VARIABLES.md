# Resumen de Variables Encapsuladas

## ✅ Variables Configuradas

Se han encapsulado **solo 3 variables esenciales**:

1. **AWS_ACCOUNT_ID** → `${env:AWS_ACCOUNT_ID, '645337731455'}`
2. **SLS_ORG** → `${env:SLS_ORG, 'darosv'}`
3. **STAGE** → `${env:STAGE, 'production'}`

## 📝 Archivos Creados

1. **serverless.common.yml** - Configuración común con las 3 variables
2. **env.template** - Template para crear archivo .env
3. **deploy-all.sh** - Script de despliegue (Linux/Mac)
4. **deploy-all.ps1** - Script de despliegue (Windows)
5. **README_VARIABLES.md** - Documentación completa

## 🔄 Cambios en serverless.yml

Todos los archivos `serverless.yml` ahora:

- Cargar configuración común: `custom: ${file(../serverless.common.yml):custom}`
- Usar `org: ${self:custom.org}`
- Usar `stage: ${self:custom.stage}`
- Usar `role: arn:aws:iam::${self:custom.awsAccountId}:role/LabRole`
- Stream ARN usa: `${self:custom.incidentesStreamArn}`

## ✅ Verificación de Código Python

**No se encontraron referencias hardcodeadas** en código Python. Todas las variables están solo en los archivos `serverless.yml`.

## 🚀 Uso

```bash
# 1. Crear .env
cp env.template .env

# 2. Editar .env con tus valores

# 3. Desplegar
./deploy-all.sh production
# o
./deploy-all.sh dev
```

## 📋 Variables en .env

```env
AWS_ACCOUNT_ID=645337731455
SLS_ORG=darosv
STAGE=production
```

¡Listo para usar!

