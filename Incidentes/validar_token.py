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
    usuarios_table_name = os.environ.get("USUARIOS_TABLE")
    tokens_table_name = os.environ.get("TOKENS_TABLE")

    if not usuarios_table_name or not tokens_table_name:
        raise RuntimeError(
            f"Faltan variables de entorno: "
            f"USUARIOS_TABLE={usuarios_table_name}, "
            f"TOKENS_TABLE={tokens_table_name}"
        )

    dynamodb = boto3.resource("dynamodb")
    return (
        dynamodb.Table(usuarios_table_name),
        dynamodb.Table(tokens_table_name),
    )


def _extract_token_from_headers(headers: dict | None):
    if not headers:
        return None

    auth = headers.get("authorization") or headers.get("Authorization")
    if not auth:
        return None

    if auth.lower().startswith("bearer "):
        return auth[7:]
    return auth


def lambda_handler(event, context):
    print("Event validarToken:", json.dumps(event))

    try:
        usuarios_table, tokens_table = _get_dynamodb_tables()

        token = _extract_token_from_headers(event.get("headers"))
        if not token:
            return _response(
                400,
                {"message": "Falta header Authorization con el token"},
            )

        try:
            res_token = tokens_table.get_item(Key={"token": token})
        except ClientError as e:
            print("Error leyendo tokens_acceso:", e)
            return _response(500, {"message": "Error interno leyendo tokens"})

        token_item = res_token.get("Item")
        if not token_item:
            return _response(200, {"valido": False})

        email = token_item.get("email")
        rol_token = token_item.get("rol")

        try:
            res_user = usuarios_table.get_item(Key={"email": email})
        except ClientError as e:
            print("Error leyendo tabla_usuarios:", e)
            return _response(500, {"message": "Error interno leyendo usuarios"})

        user = res_user.get("Item") or {}

        return _response(
            200,
            {
                "valido": True,
                "email": email,
                "rol": user.get("rol") or rol_token,
                "area": user.get("area"),
            },
        )

    except Exception as e:
        print("ERROR NO CONTROLADO en validarToken:", str(e))
        print(traceback.format_exc())
        return _response(
            500,
            {"message": "Error interno en validarToken", "detail": str(e)},
        )
