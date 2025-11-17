#!/bin/bash

# Script para actualizar automáticamente la URL del API Gateway en .env

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 Buscando URL del API Gateway...${NC}"

# Método 1: Usar serverless info
if command -v serverless >/dev/null 2>&1 && [ -f serverless.yml ]; then
    echo -e "${BLUE}📡 Intentando obtener URL desde serverless info...${NC}"
    API_URL=$(serverless info --stage prod 2>/dev/null | grep -i "HttpApiUrl" | awk '{print $2}' | head -1 | tr -d '\n')
    
    if [ -n "$API_URL" ] && [ "$API_URL" != "null" ] && [ "$API_URL" != "" ]; then
        echo -e "${GREEN}✅ URL encontrada: ${API_URL}${NC}"
        
        if [ -f .env ]; then
            # Actualizar .env
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s|^LAMBDA_API_URL=.*|LAMBDA_API_URL=${API_URL}|" .env
            else
                # Linux
                sed -i "s|^LAMBDA_API_URL=.*|LAMBDA_API_URL=${API_URL}|" .env
            fi
            echo -e "${GREEN}✅ Archivo .env actualizado${NC}"
            exit 0
        fi
    fi
fi

# Método 2: Usar AWS CLI
if command -v aws >/dev/null 2>&1; then
    echo -e "${BLUE}📡 Intentando obtener URL desde AWS CLI...${NC}"
    
    # Buscar API Gateway por nombre
    API_ID=$(aws apigatewayv2 get-apis --region us-east-1 \
        --query "Items[?contains(Name, 'airflow-assignment') || contains(Name, 'alerta-utec-airflow-assignment')].ApiId" \
        --output text 2>/dev/null | head -1 | tr -d '\n')
    
    if [ -n "$API_ID" ] && [ "$API_ID" != "None" ] && [ "$API_ID" != "" ]; then
        API_URL="https://${API_ID}.execute-api.us-east-1.amazonaws.com"
        echo -e "${GREEN}✅ URL encontrada: ${API_URL}${NC}"
        
        if [ -f .env ]; then
            # Actualizar .env
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s|^LAMBDA_API_URL=.*|LAMBDA_API_URL=${API_URL}|" .env
            else
                # Linux
                sed -i "s|^LAMBDA_API_URL=.*|LAMBDA_API_URL=${API_URL}|" .env
            fi
            echo -e "${GREEN}✅ Archivo .env actualizado${NC}"
            exit 0
        fi
    fi
fi

# Si no se encontró
echo -e "${YELLOW}⚠️  No se pudo obtener la URL automáticamente.${NC}"
echo -e "${YELLOW}   Asegúrate de que:${NC}"
echo -e "${YELLOW}   1. El servicio esté desplegado: serverless deploy${NC}"
echo -e "${YELLOW}   2. Tengas credenciales de AWS configuradas${NC}"
echo -e "${YELLOW}   3. O actualiza manualmente el archivo .env${NC}"
exit 1

