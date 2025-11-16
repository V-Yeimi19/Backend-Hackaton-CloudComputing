#!/bin/bash

################################################################################
# Script de Despliegue Automatizado - Backend Alerta UTEC
#
# Este script despliega los 3 microservicios en el orden correcto:
# 1. microservicio-reportes (crea la tabla principal con Streams)
# 2. auth (usa la tabla y crea sus propias tablas de usuarios/tokens)
# 3. alerta-realtime (escucha el Stream y hace broadcasting)
#
# Uso:
#   ./deploy.sh [stage]
#
# Ejemplos:
#   ./deploy.sh dev      # Despliega en stage 'dev'
#   ./deploy.sh prod     # Despliega en stage 'prod'
#   ./deploy.sh          # Por defecto usa 'dev'
################################################################################

set -e  # Detener ejecución si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con colores
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

# Obtener stage (por defecto 'dev')
STAGE=${1:-dev}

print_header "INICIO DE DESPLIEGUE - STAGE: $STAGE"

# Verificar que estamos en el directorio correcto
if [ ! -d "microservicio-reportes" ] || [ ! -d "auth" ] || [ ! -d "alerta-realtime" ]; then
    print_error "No se encontraron los directorios de microservicios."
    print_error "Asegúrate de ejecutar este script desde el directorio raíz del proyecto."
    exit 1
fi

# Verificar que serverless está instalado
if ! command -v serverless &> /dev/null; then
    print_error "Serverless Framework no está instalado."
    print_info "Instalando Serverless Framework..."
    npm install -g serverless
fi

print_info "Serverless Framework versión: $(serverless --version)"

################################################################################
# PASO 1: Desplegar microservicio-reportes
################################################################################
print_header "PASO 1/3: Desplegando microservicio-reportes"

cd microservicio-reportes

print_info "Verificando serverless.yml..."
if [ ! -f "serverless.yml" ]; then
    print_error "No se encontró serverless.yml en microservicio-reportes"
    exit 1
fi

print_info "Desplegando microservicio-reportes en stage '$STAGE'..."
serverless deploy --stage $STAGE --verbose

if [ $? -eq 0 ]; then
    print_success "microservicio-reportes desplegado exitosamente"

    # Capturar ARN del Stream para referencia
    print_info "Tabla creada: alerta-utec-Reporte-$STAGE"
    print_info "DynamoDB Streams: HABILITADO"
else
    print_error "Falló el despliegue de microservicio-reportes"
    exit 1
fi

cd ..

# Esperar un momento para que AWS propague los cambios
print_info "Esperando 5 segundos para propagación de recursos..."
sleep 5

################################################################################
# PASO 2: Desplegar auth
################################################################################
print_header "PASO 2/3: Desplegando auth"

cd auth

print_info "Verificando serverless.yml..."
if [ ! -f "serverless.yml" ]; then
    print_error "No se encontró serverless.yml en auth"
    exit 1
fi

print_info "Desplegando auth en stage '$STAGE'..."
serverless deploy --stage $STAGE --verbose

if [ $? -eq 0 ]; then
    print_success "auth desplegado exitosamente"

    # Capturar información de las lambdas
    print_info "Lambdas desplegadas:"
    print_info "  - api-authentication-$STAGE-register"
    print_info "  - api-authentication-$STAGE-login"
    print_info "  - api-authentication-$STAGE-validateToken"
    print_info "  - api-authentication-$STAGE-gestionTrabajadores"
    print_info "  - api-authentication-$STAGE-actualizarIncidente"
    print_info "  - api-authentication-$STAGE-obtenerHistorial"
    print_info "  - api-authentication-$STAGE-airflowValidarCambio"
    print_info "  - api-authentication-$STAGE-airflowEjecutarWorkflow"
else
    print_error "Falló el despliegue de auth"
    exit 1
fi

cd ..

# Esperar para propagación
print_info "Esperando 5 segundos para propagación de recursos..."
sleep 5

################################################################################
# PASO 3: Desplegar alerta-realtime
################################################################################
print_header "PASO 3/3: Desplegando alerta-realtime"

cd alerta-realtime

print_info "Verificando serverless.yml..."
if [ ! -f "serverless.yml" ]; then
    print_error "No se encontró serverless.yml en alerta-realtime"
    exit 1
fi

print_info "Desplegando alerta-realtime en stage '$STAGE'..."
serverless deploy --stage $STAGE --verbose

if [ $? -eq 0 ]; then
    print_success "alerta-realtime desplegado exitosamente"

    # Información del WebSocket
    print_info "WebSocket API desplegado"
    print_info "DynamoDB Stream listener: ACTIVO"
else
    print_error "Falló el despliegue de alerta-realtime"
    exit 1
fi

cd ..

################################################################################
# RESUMEN FINAL
################################################################################
print_header "DESPLIEGUE COMPLETADO EXITOSAMENTE"

print_success "Todos los microservicios fueron desplegados correctamente"
echo ""
print_info "Resumen de recursos creados:"
echo ""
echo "  📦 microservicio-reportes ($STAGE):"
echo "     - Tabla: alerta-utec-Reporte-$STAGE (con Streams)"
echo "     - Tabla: alerta-utec-AsignacionResponsables-$STAGE"
echo "     - Endpoints HTTP para gestión de reportes"
echo ""
echo "  🔐 auth ($STAGE):"
echo "     - Tabla: $STAGE-t_usuarios_hack"
echo "     - Tabla: $STAGE-t_tokens_acceso"
echo "     - Endpoints HTTP para autenticación y gestión"
echo "     - Airflow simulator endpoints"
echo ""
echo "  🔔 alerta-realtime ($STAGE):"
echo "     - Tabla: alerta-utec-connections-$STAGE"
echo "     - WebSocket API para notificaciones en tiempo real"
echo "     - Stream listener para auto-asignación de trabajadores"
echo ""

print_info "Para obtener información de endpoints, ejecuta:"
echo "  cd microservicio-reportes && serverless info --stage $STAGE"
echo "  cd auth && serverless info --stage $STAGE"
echo "  cd alerta-realtime && serverless info --stage $STAGE"
echo ""

print_info "Para ver logs en tiempo real:"
echo "  serverless logs -f [nombre-funcion] --tail --stage $STAGE"
echo ""

print_warning "IMPORTANTE: Actualiza las URLs de Airflow en auth/serverless.yml"
print_warning "La variable apiGatewayUrl necesita las URLs reales de API Gateway"
echo ""

print_success "🎉 Despliegue completado exitosamente"
