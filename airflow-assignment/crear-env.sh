#!/bin/bash

# Script para crear el archivo .env desde el template

if [ -f .env ]; then
    echo "⚠️  El archivo .env ya existe."
    read -p "¿Deseas sobrescribirlo? (s/N): " respuesta
    if [[ ! $respuesta =~ ^[Ss]$ ]]; then
        echo "Operación cancelada."
        exit 0
    fi
fi

# Copiar template a .env
cp env.template .env

echo "✅ Archivo .env creado desde env.template"
echo ""
echo "📝 Por favor edita el archivo .env y agrega tus credenciales de AWS Academy:"
echo "   1. Abre el archivo .env"
echo "   2. Completa AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY"
echo "   3. Guarda el archivo"
echo ""
echo "💡 Para obtener tus credenciales de AWS Academy:"
echo "   1. Ve a AWS Academy"
echo "   2. Accede a tu laboratorio"
echo "   3. Haz clic en 'AWS Details' o 'Show'"
echo "   4. Copia las credenciales"

