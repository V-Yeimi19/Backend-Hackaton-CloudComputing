#!/bin/bash

# Script para desplegar el servicio airflow-assignment
# Asegura que las variables de entorno estén configuradas

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Desplegando servicio airflow-assignment...${NC}\n"

# Cargar variables de entorno desde .env si existe
if [ -f .env ]; then
    echo -e "${GREEN}✅ Cargando variables de entorno desde .env${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado${NC}"
    echo -e "${YELLOW}   Usando valores por defecto${NC}"
fi

# Verificar que AWS_ACCOUNT_ID esté configurado
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo -e "${YELLOW}⚠️  AWS_ACCOUNT_ID no configurado, usando valor por defecto: 383544022422${NC}"
    export AWS_ACCOUNT_ID=383544022422
fi

# Verificar que STAGE esté configurado
if [ -z "$STAGE" ]; then
    echo -e "${YELLOW}⚠️  STAGE no configurado, usando: production${NC}"
    export STAGE=production
fi

echo -e "${BLUE}📋 Configuración:${NC}"
echo -e "   AWS_ACCOUNT_ID: ${GREEN}${AWS_ACCOUNT_ID}${NC}"
echo -e "   STAGE: ${GREEN}${STAGE}${NC}"
echo -e "   REGION: ${GREEN}us-east-1${NC}\n"

# Desplegar
echo -e "${BLUE}🔨 Desplegando con Serverless Framework...${NC}"
serverless deploy --stage ${STAGE}

echo -e "\n${GREEN}✅ Despliegue completado${NC}"

