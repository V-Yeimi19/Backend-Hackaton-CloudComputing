# 🔗 Cómo Obtener la URL del API Gateway

## Para las líneas 34-36 del `env.template`

### Paso 1: Desplegar el servicio airflow-assignment

```bash
cd Backend-Hackaton-CloudComputing/airflow-assignment
serverless deploy
```

### Paso 2: Buscar la URL en el output

Después de desplegar, verás algo como esto:

```
✔ airflow-assignment
    AsignarIncidenteEmpleadoLambdaFunctionQualifiedArn: arn:aws:lambda:us-east-1:383544022422:function:alerta-utec-airflow-assignment-prod-asignarIncidenteEmpleado:1
    ListarIncidentesEmpleadoLambdaFunctionQualifiedArn: arn:aws:lambda:us-east-1:383544022422:function:alerta-utec-airflow-assignment-prod-listarIncidentesEmpleado:1
    HttpApiId: xyz123abc
    HttpApiUrl: https://xyz123abc.execute-api.us-east-1.amazonaws.com    👈 ESTA ES LA URL QUE NECESITAS
```

### Paso 3: Copiar la URL al `.env`

Copia la URL que aparece después de `HttpApiUrl:` y pégala en el archivo `.env`:

```env
LAMBDA_API_URL=https://xyz123abc.execute-api.us-east-1.amazonaws.com
```

## ⚠️ Mientras tanto (antes de desplegar)

Puedes dejar el placeholder:

```env
LAMBDA_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com
```

El DAG de Airflow funcionará para leer de DynamoDB, pero la asignación automática no funcionará hasta que despliegues y actualices la URL.

## 📝 Nota

El formato de la URL es siempre:
```
https://{HttpApiId}.execute-api.us-east-1.amazonaws.com
```

No incluyas `/prod` o `/production` al final, solo la URL base.

