#!/bin/bash

################################################################################
# Script de Eliminación de Recursos - Backend Alerta UTEC
#
# Este script elimina TODOS los recursos desplegados en AWS.
# ADVERTENCIA: Esta acción es IRREVERSIBLE.
#
# El orden de eliminación es inverso al despliegue:
# 1. alerta-realtime (elimina listeners del Stream)
# 2. auth (elimina lambdas que usan la tabla)
# 3. microservicio-reportes (elimina la tabla principal)
#
# Uso:
#   ./destroy.sh [stage]
#
# Ejemplos:
#   ./destroy.sh dev
#   ./destroy.sh prod
################################################################################

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}$1${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
}

STAGE=${1:-dev}

print_header "ADVERTENCIA: ELIMINACIÓN DE RECURSOS"
print_warning "Este script eliminará TODOS los recursos del stage '$STAGE'"
print_warning "Esta acción es IRREVERSIBLE y eliminará:"
echo "  - Todas las tablas de DynamoDB y sus datos"
echo "  - Todas las funciones Lambda"
echo "  - Todos los endpoints de API Gateway"
echo "  - Conexiones WebSocket"
echo ""

# Confirmación del usuario
read -p "¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): " confirmation

if [ "$confirmation" != "SI" ]; then
    print_info "Operación cancelada por el usuario"
    exit 0
fi

print_header "INICIANDO ELIMINACIÓN DE RECURSOS - STAGE: $STAGE"

################################################################################
# PASO 1: Eliminar alerta-realtime
################################################################################
print_header "PASO 1/3: Eliminando alerta-realtime"

cd alerta-realtime

print_info "Eliminando stack de alerta-realtime..."
serverless remove --stage production --verbose

if [ $? -eq 0 ]; then
    print_success "alerta-realtime eliminado exitosamente"
else
    print_warning "Hubo problemas al eliminar alerta-realtime (puede que no existiera)"
fi

cd ..
sleep 3

################################################################################
# PASO 2: Eliminar auth
################################################################################
print_header "PASO 2/3: Eliminando auth"

cd auth

print_info "Eliminando stack de auth..."
serverless remove --stage $STAGE --verbose

if [ $? -eq 0 ]; then
    print_success "auth eliminado exitosamente"
else
    print_warning "Hubo problemas al eliminar auth (puede que no existiera)"
fi

cd ..
sleep 3

################################################################################
# PASO 3: Eliminar microservicio-reportes
################################################################################
print_header "PASO 3/3: Eliminando microservicio-reportes"

cd microservicio-reportes

print_info "Eliminando stack de microservicio-reportes..."
serverless remove --stage $STAGE --verbose

if [ $? -eq 0 ]; then
    print_success "microservicio-reportes eliminado exitosamente"
else
    print_warning "Hubo problemas al eliminar microservicio-reportes (puede que no existiera)"
fi

cd ..

################################################################################
# RESUMEN FINAL
################################################################################
print_header "ELIMINACIÓN COMPLETADA"

print_success "Todos los recursos han sido eliminados"
echo ""
print_info "Recursos eliminados:"
echo "  ✓ Tablas de DynamoDB"
echo "  ✓ Funciones Lambda"
echo "  ✓ API Gateways (HTTP y WebSocket)"
echo "  ✓ Roles y políticas IAM asociadas"
echo ""

print_info "Para verificar que todo fue eliminado, revisa la consola de AWS:"
echo "  - DynamoDB: https://console.aws.amazon.com/dynamodb"
echo "  - Lambda: https://console.aws.amazon.com/lambda"
echo "  - API Gateway: https://console.aws.amazon.com/apigateway"
echo ""

print_success "🗑️  Limpieza completada exitosamente"
