import json
import os
import boto3
import traceback
from botocore.exceptions import ClientError


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,DELETE",
        },
        "body": json.dumps(body),
    }


def _get_dynamodb_tables():
    incidentes_table_name = os.environ.get("INCIDENTES_TABLE")
    usuarios_table_name = os.environ.get("USUARIOS_TABLE")
    tokens_table_name = os.environ.get("TOKENS_TABLE")

    if not incidentes_table_name or not usuarios_table_name or not tokens_table_name:
        raise RuntimeError(
            f"Faltan variables de entorno: "
            f"INCIDENTES_TABLE={incidentes_table_name}, "
            f"USUARIOS_TABLE={usuarios_table_name}, "
            f"TOKENS_TABLE={tokens_table_name}"
        )

    dynamodb = boto3.resource("dynamodb")
    return (
        dynamodb.Table(incidentes_table_name),
        dynamodb.Table(usuarios_table_name),
        dynamodb.Table(tokens_table_name),
    )


def _extract_token_from_headers(headers):
    if not headers:
        return None

    auth = headers.get("authorization") or headers.get("Authorization")
    if not auth:
        return None

    if auth.lower().startswith("bearer "):
        return auth[7:]
    return auth


def _validar_token_y_obtener_usuario(token, tokens_table, usuarios_table):
    try:
        res_token = tokens_table.get_item(Key={"token": token})
    except ClientError as e:
        print("Error leyendo tokens_acceso:", e)
        return None, "Error interno leyendo tokens"

    token_item = res_token.get("Item")
    if not token_item:
        return None, "Token inválido o expirado"

    email = token_item.get("email")
    if not email:
        return None, "Token inválido (sin email)"

    try:
        res_user = usuarios_table.get_item(Key={"email": email})
    except ClientError as e:
        print("Error leyendo tabla_usuarios:", e)
        return None, "Error interno leyendo usuarios"

    user = res_user.get("Item")
    if not user:
        return None, "Usuario asociado al token no encontrado"

    user_info = {
        "email": email,
        "rol": user.get("rol") or token_item.get("rol"),
        "area": user.get("area"),
    }
    return user_info, None


def lambda_handler(event, context):
    print("Event eliminarIncidente:", json.dumps(event))

    try:
        incidentes_table, usuarios_table, tokens_table = _get_dynamodb_tables()

        # 1. Token desde el header
        token = _extract_token_from_headers(event.get("headers"))
        if not token:
            return _response(
                401,
                {"message": "Falta header Authorization con el token"},
            )

        # 2. Validar token y obtener usuario
        user_info, error = _validar_token_y_obtener_usuario(
            token, tokens_table, usuarios_table
        )
        if error:
            return _response(401, {"message": error})

        # 3. Verificar rol administrador
        if (user_info.get("rol") or "").lower() != "administrativo":
            return _response(
                403,
                {"message": "No tiene permisos para eliminar incidentes"},
            )

        # 4. Obtener id de pathParameters
        path_params = event.get("pathParameters") or {}
        incidente_id = path_params.get("id")

        if not incidente_id:
            return _response(400, {"message": "Falta path parameter 'id'"})

        # 5. Verificar que el incidente exista
        try:
            res = incidentes_table.get_item(Key={"id": incidente_id})
            if "Item" not in res:
                return _response(404, {"message": "Incidente no encontrado"})
        except ClientError as e:
            print("Error leyendo incidente:", e)
            return _response(500, {"message": "Error interno leyendo incidente"})

        # 6. Eliminar incidente
        try:
            incidentes_table.delete_item(Key={"id": incidente_id})
        except ClientError as e:
            print("Error eliminando incidente:", e)
            return _response(500, {"message": "Error interno eliminando incidente"})

        return _response(
            200,
            {"message": "Incidente eliminado correctamente", "id": incidente_id},
        )

    except Exception as e:
        print("ERROR NO CONTROLADO en eliminarIncidente:", str(e))
        print(traceback.format_exc())
        return _response(
            500,
            {"message": "Error interno en eliminarIncidente", "detail": str(e)},
        )
