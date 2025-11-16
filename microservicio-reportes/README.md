# Microservicio de Reportes - AlertaUTEC

Microservicio independiente para la gestión completa de reportes de incidentes.

## 🎯 Responsabilidades

- ✅ CRUD completo de reportes
- ✅ Gestión de asignaciones de responsables
- ✅ Validación de datos de entrada
- ✅ Creación y gestión de tablas DynamoDB

## 📁 Estructura

```
microservicio-reportes/
├── serverless.yml          # Configuración del servicio
├── requirements.txt        # Dependencias Python
└── reportes/              # Funciones Lambda
    ├── crearReporte.py
    ├── obtenerReporte.py
    ├── listarReportes.py
    ├── actualizarReporte.py
    ├── eliminarReporte.py
    ├── actualizarEstadoReporte.py
    ├── asignarResponsables.py
    └── obtenerResponsables.py
```

## 🚀 Despliegue

```bash
cd microservicio-reportes
pip install -r requirements.txt
serverless deploy
```

## 📡 Endpoints

| Método | Path | Descripción |
|--------|------|-------------|
| POST | `/reportes` | Crear reporte |
| GET | `/reportes` | Listar reportes |
| GET | `/reportes/{id}` | Obtener reporte |
| PUT | `/reportes/{id}` | Actualizar reporte |
| DELETE | `/reportes/{id}` | Eliminar reporte |
| PATCH | `/reportes/{id}/estado` | Actualizar estado |
| POST | `/reportes/{id}/asignar` | Asignar responsables |
| GET | `/reportes/{id}/responsables` | Obtener responsables |

## 🗄️ Recursos Creados

- **DynamoDB Tables:**
  - `alerta-utec-Reporte-{stage}`
  - `alerta-utec-AsignacionResponsables-{stage}`

## ⚙️ Variables de Entorno

- `REPORTES_TABLE`: Nombre de la tabla de reportes
- `ASIGNACIONES_TABLE`: Nombre de la tabla de asignaciones

## 🔗 Dependencias

Este microservicio **no depende** de otros servicios. Es completamente independiente.

