# Script PowerShell para configurar y ejecutar Airflow
# Compatible con AWS Academy

$ErrorActionPreference = "Stop"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Cyan "🚀 Configurando Airflow para AlertaUTEC`n"

# Verificar requisitos
Write-ColorOutput Cyan "📋 Verificando requisitos...`n"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "❌ Docker no está instalado. Por favor instálalo primero."
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-ColorOutput Red "❌ Docker Compose no está instalado. Por favor instálalo primero."
    exit 1
}

Write-ColorOutput Green "✅ Docker y Docker Compose están instalados`n"

# Verificar que Docker está ejecutándose
try {
    docker info | Out-Null
    Write-ColorOutput Green "✅ Docker está ejecutándose`n"
} catch {
    Write-ColorOutput Red "❌ Docker no está ejecutándose. Por favor inicia Docker Desktop."
    exit 1
}

# Crear directorios necesarios
Write-ColorOutput Cyan "📁 Creando directorios necesarios...`n"
New-Item -ItemType Directory -Force -Path logs, plugins, config | Out-Null
Write-ColorOutput Green "✅ Directorios creados`n"

# Configurar variables de entorno para AWS Academy
Write-ColorOutput Cyan "🔐 Configurando credenciales de AWS Academy...`n"

$AWS_ACCESS_KEY_ID = $env:AWS_ACCESS_KEY_ID
$AWS_SECRET_ACCESS_KEY = $env:AWS_SECRET_ACCESS_KEY
$AWS_DEFAULT_REGION = $env:AWS_DEFAULT_REGION

# Intentar obtener credenciales de AWS CLI
if (Get-Command aws -ErrorAction SilentlyContinue) {
    try {
        $awsProfile = aws configure list --profile default 2>$null
        if ($awsProfile -match "access_key") {
            Write-ColorOutput Green "✅ Credenciales de AWS encontradas`n"
            
            $AWS_ACCESS_KEY_ID = aws configure get aws_access_key_id 2>$null
            $AWS_SECRET_ACCESS_KEY = aws configure get aws_secret_access_key 2>$null
            $AWS_DEFAULT_REGION = aws configure get region 2>$null
            if (-not $AWS_DEFAULT_REGION) {
                $AWS_DEFAULT_REGION = "us-east-1"
            }
        }
    } catch {
        Write-ColorOutput Yellow "⚠️  No se pudieron obtener credenciales de AWS CLI`n"
    }
}

# Crear archivo .env
if ($AWS_ACCESS_KEY_ID -and $AWS_SECRET_ACCESS_KEY) {
    $envContent = @"
# Variables de AWS (desde AWS CLI/Academy)
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION

# Variables de DynamoDB
INCIDENTES_TABLE=Incidentes
USUARIOS_TABLE=tabla_usuarios

# URL del API Gateway (actualizar después de desplegar los Lambdas)
LAMBDA_API_URL=https://your-api.execute-api.us-east-1.amazonaws.com/production

# Nombre del Lambda de asignación (actualizar después de desplegar)
LAMBDA_ASIGNAR_FUNCTION=alerta-utec-airflow-assignment-production-asignarIncidenteEmpleado
"@
    Set-Content -Path .env -Value $envContent
    Write-ColorOutput Green "✅ Archivo .env creado con credenciales de AWS`n"
} else {
    Write-ColorOutput Yellow "⚠️  No se encontraron credenciales de AWS`n"
    Write-ColorOutput Yellow "   El DAG puede no funcionar correctamente sin acceso a DynamoDB`n"
    Write-ColorOutput Yellow "   Puedes configurarlas después en el archivo .env`n`n"
    
    $envContent = @"
# Variables de AWS (configurar con tus credenciales de AWS Academy)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1

# Variables de DynamoDB
INCIDENTES_TABLE=Incidentes
USUARIOS_TABLE=tabla_usuarios

# URL del API Gateway (actualizar después de desplegar los Lambdas)
LAMBDA_API_URL=https://your-api.execute-api.us-east-1.amazonaws.com/production

# Nombre del Lambda de asignación (actualizar después de desplegar)
LAMBDA_ASIGNAR_FUNCTION=alerta-utec-airflow-assignment-production-asignarIncidenteEmpleado
"@
    Set-Content -Path .env -Value $envContent
    Write-ColorOutput Cyan "📝 Archivo .env creado. Por favor edítalo con tus credenciales.`n"
}

# Construir imágenes Docker
Write-ColorOutput Cyan "🔨 Construyendo imágenes Docker (esto puede tardar varios minutos)...`n"
docker-compose build
Write-ColorOutput Green "✅ Imágenes construidas`n"

# Inicializar Airflow
Write-ColorOutput Cyan "🔧 Inicializando Airflow (creando base de datos y usuario admin)...`n"
docker-compose up airflow-init
Write-ColorOutput Green "✅ Airflow inicializado`n"

# Iniciar servicios
Write-ColorOutput Cyan "🚀 Iniciando servicios de Airflow...`n"
docker-compose up -d
Write-ColorOutput Green "✅ Servicios iniciados`n"

# Esperar a que los servicios estén listos
Write-ColorOutput Cyan "⏳ Esperando a que los servicios estén listos (30 segundos)...`n"
Start-Sleep -Seconds 30

# Verificar estado
Write-ColorOutput Cyan "🔍 Verificando estado de los servicios...`n"
docker-compose ps

# Verificar que el webserver está respondiendo
Write-ColorOutput Cyan "`n🌐 Verificando que el webserver está funcionando...`n"
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/health" -UseBasicParsing -TimeoutSec 5
    Write-ColorOutput Green "✅ Webserver está funcionando correctamente`n"
} catch {
    Write-ColorOutput Yellow "⚠️  El webserver aún no está listo. Espera unos segundos más.`n"
}

# Mostrar información de acceso
Write-ColorOutput Green "═══════════════════════════════════════════════════════════"
Write-ColorOutput Green "✅ Airflow está configurado y ejecutándose`n"
Write-ColorOutput Cyan "📊 Accede a la interfaz web en:"
Write-ColorOutput Green "   http://localhost:8080`n"
Write-ColorOutput Cyan "🔑 Credenciales:"
Write-ColorOutput Green "   Usuario: admin"
Write-ColorOutput Green "   Contraseña: admin`n"
Write-ColorOutput Cyan "📝 Próximos pasos:"
Write-Output "   1. Abre http://localhost:8080 en tu navegador"
Write-Output "   2. Busca el DAG 'asignacion_automatica_incidentes'"
Write-Output "   3. Actívalo haciendo clic en el toggle de pausa"
Write-Output "   4. El DAG se ejecutará automáticamente cada 2 minutos`n"
Write-ColorOutput Cyan "🛠️  Comandos útiles:"
Write-ColorOutput Green "   Ver logs: docker-compose logs -f"
Write-ColorOutput Green "   Detener: docker-compose down"
Write-ColorOutput Green "   Reiniciar: docker-compose restart"
Write-ColorOutput Green "═══════════════════════════════════════════════════════════`n"

# Mostrar logs recientes
Write-ColorOutput Cyan "📋 Últimos logs del scheduler:"
docker-compose logs --tail=20 airflow-scheduler

Write-Output "`n"
Write-ColorOutput Green "✨ ¡Listo! Airflow está ejecutándose.`n"

