# 🚀 Instrucciones para Ejecutar Airflow

## 📋 Requisitos Previos

1. **Docker Desktop** instalado y ejecutándose
2. **AWS CLI** configurado (opcional, solo si usas AWS)
3. Variables de entorno de AWS (si necesitas acceder a DynamoDB)

## 📝 Pasos para Ejecutar

### Paso 1: Navegar al directorio

```bash
cd Backend-Hackaton-CloudComputing/airflow-assignment
```

### Paso 2: Crear directorios necesarios

```bash
# Windows (PowerShell)
mkdir logs, plugins, config

# Linux/Mac
mkdir -p logs plugins config
```

### Paso 3: Configurar variables de entorno (opcional)

Crea un archivo `.env` en el directorio `airflow-assignment`:

```bash
# Windows (PowerShell)
New-Item .env

# Linux/Mac
touch .env
```

Edita el archivo `.env` con tus credenciales:

```env
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_DEFAULT_REGION=us-east-1
LAMBDA_API_URL=https://tu-api.execute-api.us-east-1.amazonaws.com/production
```

**Nota**: Si no tienes credenciales de AWS, puedes omitir este paso, pero el DAG no podrá acceder a DynamoDB.

### Paso 4: Construir las imágenes Docker

```bash
docker-compose build
```

Esto puede tardar varios minutos la primera vez.

### Paso 5: Inicializar Airflow

```bash
docker-compose up airflow-init
```

Esto creará la base de datos y el usuario administrador.

### Paso 6: Iniciar Airflow

```bash
docker-compose up -d
```

El flag `-d` ejecuta los contenedores en segundo plano.

### Paso 7: Verificar que está funcionando

Espera unos segundos y luego verifica los logs:

```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs solo del webserver
docker-compose logs airflow-webserver

# Ver logs solo del scheduler
docker-compose logs airflow-scheduler
```

### Paso 8: Acceder a la interfaz web

Abre tu navegador y ve a:

```
http://localhost:8080
```

**Credenciales:**
- Usuario: `admin`
- Contraseña: `admin`

## 🛠️ Comandos Útiles

### Ver estado de los contenedores

```bash
docker-compose ps
```

### Detener Airflow

```bash
docker-compose down
```

### Detener y eliminar volúmenes (reiniciar desde cero)

```bash
docker-compose down -v
```

### Ver logs en tiempo real

```bash
docker-compose logs -f
```

### Reiniciar un servicio específico

```bash
docker-compose restart airflow-scheduler
docker-compose restart airflow-webserver
```

### Ejecutar comandos dentro del contenedor

```bash
# Acceder al contenedor del scheduler
docker-compose exec airflow-scheduler bash

# Listar DAGs
docker-compose exec airflow-scheduler airflow dags list

# Activar un DAG manualmente
docker-compose exec airflow-scheduler airflow dags unpause asignacion_automatica_incidentes
```

## 🔍 Verificar que el DAG está funcionando

1. En la interfaz web de Airflow (http://localhost:8080)
2. Busca el DAG `asignacion_automatica_incidentes`
3. Si está pausado (pausa icon), haz clic en el toggle para activarlo
4. El DAG se ejecutará automáticamente cada 2 minutos

## ⚠️ Solución de Problemas

### Error: "Port 8080 is already in use"

```bash
# Windows
netstat -ano | findstr :8080
# Luego mata el proceso con el PID encontrado

# Linux/Mac
lsof -i :8080
kill -9 <PID>
```

O cambia el puerto en `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"  # Cambiar 8080 por 8081
```

### Error: "Permission denied" en logs o plugins

```bash
# Linux/Mac
sudo chown -R 50000:0 logs plugins config

# O elimina y recrea los directorios
rm -rf logs plugins config
mkdir -p logs plugins config
```

### El DAG no aparece

1. Verifica que el archivo está en `dags/asignacion_automatica.py`
2. Revisa los logs del scheduler:
   ```bash
   docker-compose logs airflow-scheduler | grep -i error
   ```
3. Verifica la sintaxis del DAG:
   ```bash
   docker-compose exec airflow-scheduler python /opt/airflow/dags/asignacion_automatica.py
   ```

### Error de conexión a DynamoDB

1. Verifica que las credenciales de AWS están correctas en `.env`
2. Verifica que tienes permisos para leer DynamoDB
3. Revisa los logs:
   ```bash
   docker-compose logs airflow-scheduler | grep -i dynamodb
   ```

## 📊 Monitoreo

### Ver métricas del DAG

En la interfaz web:
- Haz clic en el nombre del DAG
- Ve a la pestaña "Graph" para ver el flujo
- Ve a "Logs" para ver los logs de cada tarea

### Ver logs desde la consola

```bash
# Logs del scheduler (donde se ejecutan los DAGs)
docker-compose logs -f airflow-scheduler

# Logs del webserver
docker-compose logs -f airflow-webserver
```

## 🎯 Próximos Pasos

1. **Activar el DAG**: En la UI, desactiva la pausa del DAG
2. **Configurar variables**: Ve a Admin > Variables y agrega:
   - `LAMBDA_ASIGNAR_FUNCTION`: nombre del Lambda después de desplegar
3. **Monitorear ejecuciones**: Ve a la pestaña "DAG Runs" para ver el historial

## 📚 Recursos

- [Documentación de Airflow](https://airflow.apache.org/docs/)
- [Docker Compose Docs](https://docs.docker.com/compose/)

