#!/bin/bash

# Script de automatización para configurar y ejecutar Airflow
# Compatible con AWS Academy

set -e  # Salir si hay algún error

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Configurando Airflow para AlertaUTEC${NC}\n"

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar requisitos
echo -e "${BLUE}📋 Verificando requisitos...${NC}"

if ! command_exists docker; then
    echo -e "${RED}❌ Docker no está instalado. Por favor instálalo primero.${NC}"
    exit 1
fi

# Verificar docker-compose (puede ser 'docker-compose' o 'docker compose')
DOCKER_COMPOSE_CMD=""
if command_exists docker-compose; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo -e "${YELLOW}ℹ️  Usando 'docker compose' (versión nueva)${NC}"
else
    echo -e "${RED}❌ Docker Compose no está instalado.${NC}"
    echo -e "${YELLOW}📦 Instalación rápida:${NC}"
    echo -e "   ${GREEN}sudo apt-get update && sudo apt-get install -y docker.io docker-compose${NC}"
    echo -e "   ${GREEN}sudo usermod -aG docker \$USER${NC}"
    echo -e "   ${GREEN}newgrp docker${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker y Docker Compose están instalados${NC}\n"

# Verificar que Docker está ejecutándose
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker no está ejecutándose. Por favor inicia Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker está ejecutándose${NC}\n"

# Crear directorios necesarios
echo -e "${BLUE}📁 Creando directorios necesarios...${NC}"
mkdir -p logs plugins config
echo -e "${GREEN}✅ Directorios creados${NC}\n"

# Configurar variables de entorno para AWS Academy
echo -e "${BLUE}🔐 Configurando credenciales de AWS Academy...${NC}"

# Intentar obtener credenciales de AWS Academy
if command_exists aws; then
    # Verificar si hay un perfil de AWS configurado
    if aws configure list --profile default 2>/dev/null | grep -q "access_key"; then
        echo -e "${GREEN}✅ Credenciales de AWS encontradas${NC}"
        
        # Obtener credenciales del perfil actual
        AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id 2>/dev/null || echo "")
        AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key 2>/dev/null || echo "")
        AWS_SESSION_TOKEN=$(aws configure get aws_session_token 2>/dev/null || echo "")
        AWS_DEFAULT_REGION=$(aws configure get region 2>/dev/null || echo "us-east-1")
        
        if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
            export AWS_ACCESS_KEY_ID
            export AWS_SECRET_ACCESS_KEY
            export AWS_DEFAULT_REGION
            if [ -n "$AWS_SESSION_TOKEN" ]; then
                export AWS_SESSION_TOKEN
            fi
            echo -e "${GREEN}✅ Credenciales de AWS configuradas desde AWS CLI${NC}"
        fi
    fi
fi

# Si no se encontraron credenciales, intentar desde variables de entorno
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    if [ -n "${AWS_ACCESS_KEY_ID}" ] && [ -n "${AWS_SECRET_ACCESS_KEY}" ]; then
        echo -e "${GREEN}✅ Credenciales de AWS encontradas en variables de entorno${NC}"
    else
        echo -e "${YELLOW}⚠️  No se encontraron credenciales de AWS${NC}"
        echo -e "${YELLOW}   El DAG puede no funcionar correctamente sin acceso a DynamoDB${NC}"
        echo -e "${YELLOW}   Puedes configurarlas después en el archivo .env${NC}\n"
        
        # El archivo .env ya existe, solo informar
        echo -e "${BLUE}📝 Archivo .env existe. Por favor edítalo con tus credenciales de AWS Academy.${NC}\n"
    fi
fi

# Si tenemos credenciales, actualizar .env
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    # Actualizar solo las credenciales en .env si existe, o crear uno nuevo
    if [ -f .env ]; then
        # Actualizar credenciales en .env existente
        sed -i.bak "s/^AWS_ACCESS_KEY_ID=.*/AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}/" .env
        sed -i.bak "s/^AWS_SECRET_ACCESS_KEY=.*/AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}/" .env
        sed -i.bak "s/^AWS_DEFAULT_REGION=.*/AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}/" .env
        if [ -n "$AWS_SESSION_TOKEN" ]; then
            # Si existe AWS_SESSION_TOKEN en .env, actualizarlo; si no, agregarlo
            if grep -q "^AWS_SESSION_TOKEN=" .env; then
                sed -i.bak "s|^AWS_SESSION_TOKEN=.*|AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}|" .env
            else
                sed -i.bak "/^AWS_DEFAULT_REGION=/a AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}" .env
            fi
        fi
        rm -f .env.bak 2>/dev/null
        echo -e "${GREEN}✅ Archivo .env actualizado con credenciales de AWS${NC}\n"
    else
        # Crear .env desde el template
        if [ -f env.template ]; then
            cp env.template .env
        else
            cat > .env << EOF
# Variables de AWS (desde AWS CLI/Academy)
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}

# Variables de DynamoDB
INCIDENTES_TABLE=Incidentes
USUARIOS_TABLE=tabla_usuarios

# URL del API Gateway (actualizar después de desplegar los Lambdas)
LAMBDA_API_URL=https://your-api.execute-api.us-east-1.amazonaws.com/production

# Nombre del Lambda de asignación (actualizar después de desplegar)
LAMBDA_ASIGNAR_FUNCTION=alerta-utec-airflow-assignment-production-asignarIncidenteEmpleado
EOF
        echo -e "${GREEN}✅ Archivo .env creado con credenciales de AWS${NC}\n"
    fi
fi

# Intentar obtener la URL del API Gateway si el servicio está desplegado
echo -e "${BLUE}🔍 Verificando si el servicio airflow-assignment está desplegado...${NC}"
if command_exists serverless && [ -f serverless.yml ]; then
    # Intentar obtener la URL del API Gateway
    API_URL=$(serverless info --stage prod 2>/dev/null | grep -i "HttpApiUrl" | awk '{print $2}' | head -1)
    
    if [ -n "$API_URL" ] && [ "$API_URL" != "null" ]; then
        echo -e "${GREEN}✅ URL del API Gateway encontrada: ${API_URL}${NC}"
        
        # Actualizar .env con la URL real
        if [ -f .env ]; then
            sed -i.bak "s|^LAMBDA_API_URL=.*|LAMBDA_API_URL=${API_URL}|" .env
            rm -f .env.bak 2>/dev/null
            echo -e "${GREEN}✅ Archivo .env actualizado con la URL del API Gateway${NC}\n"
        fi
    else
        # Intentar obtener usando AWS CLI
        if command_exists aws; then
            echo -e "${YELLOW}⚠️  Intentando obtener URL desde AWS...${NC}"
            # Buscar el API Gateway por nombre
            API_ID=$(aws apigatewayv2 get-apis --region us-east-1 --query "Items[?contains(Name, 'airflow-assignment') || contains(Name, 'alerta-utec-airflow')].ApiId" --output text 2>/dev/null | head -1)
            
            if [ -n "$API_ID" ] && [ "$API_ID" != "None" ]; then
                API_URL="https://${API_ID}.execute-api.us-east-1.amazonaws.com"
                echo -e "${GREEN}✅ URL del API Gateway encontrada: ${API_URL}${NC}"
                
                if [ -f .env ]; then
                    sed -i.bak "s|^LAMBDA_API_URL=.*|LAMBDA_API_URL=${API_URL}|" .env
                    rm -f .env.bak 2>/dev/null
                    echo -e "${GREEN}✅ Archivo .env actualizado con la URL del API Gateway${NC}\n"
                fi
            else
                echo -e "${YELLOW}⚠️  Servicio no desplegado aún. Debes desplegarlo primero:${NC}"
                echo -e "${YELLOW}   cd airflow-assignment && serverless deploy${NC}"
                echo -e "${YELLOW}   Luego ejecuta este script nuevamente.${NC}\n"
            fi
        else
            echo -e "${YELLOW}⚠️  Servicio no desplegado aún o no se pudo obtener la URL.${NC}"
            echo -e "${YELLOW}   Despliega el servicio con: serverless deploy${NC}\n"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Serverless Framework no encontrado o no estás en el directorio correcto.${NC}"
    echo -e "${YELLOW}   La URL se actualizará manualmente después de desplegar.${NC}\n"
fi

# Construir imágenes Docker
echo -e "${BLUE}🔨 Construyendo imágenes Docker (esto puede tardar varios minutos)...${NC}"
$DOCKER_COMPOSE_CMD build
echo -e "${GREEN}✅ Imágenes construidas${NC}\n"

# Inicializar Airflow
echo -e "${BLUE}🔧 Inicializando Airflow (creando base de datos y usuario admin)...${NC}"
$DOCKER_COMPOSE_CMD up airflow-init
echo -e "${GREEN}✅ Airflow inicializado${NC}\n"

# Iniciar servicios
echo -e "${BLUE}🚀 Iniciando servicios de Airflow...${NC}"
$DOCKER_COMPOSE_CMD up -d
echo -e "${GREEN}✅ Servicios iniciados${NC}\n"

# Esperar a que los servicios estén listos
echo -e "${BLUE}⏳ Esperando a que los servicios estén listos (30 segundos)...${NC}"
sleep 30

# Verificar estado
echo -e "${BLUE}🔍 Verificando estado de los servicios...${NC}"
$DOCKER_COMPOSE_CMD ps

# Verificar que el webserver está respondiendo
echo -e "\n${BLUE}🌐 Verificando que el webserver está funcionando...${NC}"
if curl -s -f http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Webserver está funcionando correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  El webserver aún no está listo. Espera unos segundos más.${NC}"
fi

# Mostrar información de acceso
echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Airflow está configurado y ejecutándose${NC}\n"
echo -e "${BLUE}📊 Accede a la interfaz web en:${NC}"
echo -e "   ${GREEN}http://localhost:8080${NC}\n"
echo -e "${BLUE}🔑 Credenciales:${NC}"
echo -e "   Usuario: ${GREEN}admin${NC}"
echo -e "   Contraseña: ${GREEN}admin${NC}\n"
echo -e "${BLUE}📝 Próximos pasos:${NC}"
echo -e "   1. Abre http://localhost:8080 en tu navegador"
echo -e "   2. Busca el DAG 'asignacion_automatica_incidentes'"
echo -e "   3. Actívalo haciendo clic en el toggle de pausa"
echo -e "   4. El DAG se ejecutará automáticamente cada 2 minutos\n"
echo -e "${BLUE}🛠️  Comandos útiles:${NC}"
echo -e "   Ver logs: ${GREEN}docker-compose logs -f${NC}"
echo -e "   Detener: ${GREEN}docker-compose down${NC}"
echo -e "   Reiniciar: ${GREEN}docker-compose restart${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

# Mostrar logs recientes
echo -e "${BLUE}📋 Últimos logs del scheduler:${NC}"
$DOCKER_COMPOSE_CMD logs --tail=20 airflow-scheduler

echo -e "\n${GREEN}✨ ¡Listo! Airflow está ejecutándose.${NC}\n"
