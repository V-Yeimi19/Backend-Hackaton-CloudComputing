import json
import os
import boto3
import traceback
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "OPTIONS,GET",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    """
    Lambda para que un empleado vea:
    1. Incidentes asignados a él
    2. Incidentes de su categoría/área (sin asignar)
    
    Query params:
    - empleadoEmail: email del empleado
    - tipo: "asignados" | "disponibles" | "todos"
    """
    print("Event listarIncidentesEmpleado:", json.dumps(event))

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

        # Obtener query params
        query_params = event.get("queryStringParameters") or {}
        empleado_email = query_params.get("empleadoEmail")
        tipo = query_params.get("tipo", "todos")  # asignados, disponibles, todos

        if not empleado_email:
            return _response(400, {"message": "Query param obligatorio: empleadoEmail"})

        # Verificar que el empleado existe
        try:
            res_user = usuarios_table.get_item(Key={"email": empleado_email})
        except ClientError as e:
            print("Error leyendo tabla_usuarios:", e)
            return _response(500, {"message": "Error interno leyendo usuarios"})

        user = res_user.get("Item")
        if not user:
            return _response(404, {"message": "Empleado no encontrado"})

        empleado_area = user.get("area")

        # Filtrar incidentes según el tipo
        try:
            if tipo == "asignados":
                # Solo incidentes asignados a este empleado
                response = incidentes_table.scan(
                    FilterExpression=Attr("asignadoA").eq(empleado_email)
                )
            elif tipo == "disponibles":
                # Incidentes de su área sin asignar
                response = incidentes_table.scan(
                    FilterExpression=Attr("areaResponsable").eq(empleado_area)
                    & Attr("asignadoA").not_exists()
                )
            else:  # todos
                # Todos los incidentes de su área (asignados a él o sin asignar)
                response = incidentes_table.scan(
                    FilterExpression=Attr("areaResponsable").eq(empleado_area)
                )

            incidentes = response.get("Items", [])

            # Ordenar por fecha de creación (más recientes primero)
            incidentes.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

            return _response(
                200,
                {
                    "message": "Incidentes obtenidos correctamente",
                    "empleadoEmail": empleado_email,
                    "empleadoArea": empleado_area,
                    "tipo": tipo,
                    "total": len(incidentes),
                    "incidentes": incidentes,
                },
            )

        except ClientError as e:
            print("Error escaneando incidentes:", e)
            return _response(500, {"message": "Error interno leyendo incidentes"})

    except Exception as e:
        print("ERROR NO CONTROLADO en listarIncidentesEmpleado:", str(e))
        print(traceback.format_exc())
        return _response(
            500,
            {
                "message": "Error interno en listarIncidentesEmpleado",
                "detail": str(e),
            },
        )

