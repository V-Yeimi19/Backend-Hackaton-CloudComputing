FROM apache/airflow:2.8.0

USER root

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Instalar dependencias de Python
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copiar DAGs
COPY dags/ /opt/airflow/dags/

