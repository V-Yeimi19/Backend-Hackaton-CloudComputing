import json
import os
import boto3
import traceback
from datetime import datetime
from botocore.exceptions import ClientError


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,PUT",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    """
    Lambda para asignar un incidente a un empleado específico.
    Llamado por Airflow cuando encuentra un empleado disponible.
    
    Body esperado:
    {
        "incidenteId": "uuid",
        "empleadoEmail": "empleado@example.com"
    }
    """
    print("Event asignarIncidenteEmpleado:", json.dumps(event))

    try:
        incidentes_table_name = os.environ.get("INCIDENTES_TABLE")
        usuarios_table_name = os.environ.get("USUARIOS_TABLE")

        if not incidentes_table_name or not usuarios_table_name:
            raise RuntimeError(
                f"Faltan variables de entorno: "
                f"INCIDENTES_TABLE={incidentes_table_name}, "
                f"USUARIOS_TABLE={usuarios_table_name}"
            )

        dynamodb = boto3.resource("dynamodb")
        incidentes_table = dynamodb.Table(incidentes_table_name)
        usuarios_table = dynamodb.Table(usuarios_table_name)

        # Obtener incidente_id del path o del body
        path_params = event.get("pathParameters") or {}
        incidente_id = path_params.get("id")
        
        # Obtener body
        try:
            body = json.loads(event.get("body") or "{}")
        except json.JSONDecodeError:
            return _response(400, {"message": "El body debe ser JSON"})

        # Si no viene en path, intentar del body
        if not incidente_id:
            incidente_id = body.get("incidenteId")
        
        empleado_email = body.get("empleadoEmail")

        if not incidente_id or not empleado_email:
            return _response(
                400,
                {"message": "Campos obligatorios: incidenteId, empleadoEmail"},
            )

        # Verificar que el empleado existe y es trabajador
        try:
            res_user = usuarios_table.get_item(Key={"email": empleado_email})
        except ClientError as e:
            print("Error leyendo tabla_usuarios:", e)
            return _response(500, {"message": "Error interno leyendo usuarios"})

        user = res_user.get("Item")
        if not user:
            return _response(404, {"message": "Empleado no encontrado"})

        if user.get("rol") != "trabajador":
            return _response(400, {"message": "El usuario no es un trabajador"})

        # Verificar que el incidente existe
        try:
            res_incidente = incidentes_table.get_item(Key={"id": incidente_id})
        except ClientError as e:
            print("Error leyendo tabla_incidentes:", e)
            return _response(500, {"message": "Error interno leyendo incidentes"})

        incidente = res_incidente.get("Item")
        if not incidente:
            return _response(404, {"message": "Incidente no encontrado"})

        # Verificar que el área del empleado coincide con el área responsable del incidente
        empleado_area = user.get("area")
        incidente_area = incidente.get("areaResponsable")

        if empleado_area != incidente_area:
            return _response(
                400,
                {
                    "message": f"El área del empleado ({empleado_area}) no coincide con el área del incidente ({incidente_area})"
                },
            )

        # Verificar que el incidente no esté ya asignado
        if incidente.get("asignadoA"):
            return _response(
                409,
                {
                    "message": f"El incidente ya está asignado a {incidente.get('asignadoA')}"
                },
            )

        # Actualizar el incidente con la asignación
        now = datetime.utcnow().isoformat()
        try:
            incidentes_table.update_item(
                Key={"id": incidente_id},
                UpdateExpression="SET asignadoA = :email, asignadoEn = :fecha, estado = :estado, updatedAt = :updatedAt",
                ExpressionAttributeValues={
                    ":email": empleado_email,
                    ":fecha": now,
                    ":estado": "En atencion",
                    ":updatedAt": now,
                },
                ReturnValues="ALL_NEW",
            )
        except ClientError as e:
            print("Error actualizando incidente:", e)
            return _response(500, {"message": "Error interno actualizando incidente"})

        return _response(
            200,
            {
                "message": "Incidente asignado correctamente",
                "incidenteId": incidente_id,
                "empleadoEmail": empleado_email,
                "asignadoEn": now,
            },
        )

    except Exception as e:
        print("ERROR NO CONTROLADO en asignarIncidenteEmpleado:", str(e))
        print(traceback.format_exc())
        return _response(
            500,
            {
                "message": "Error interno en asignarIncidenteEmpleado",
                "detail": str(e),
            },
        )

