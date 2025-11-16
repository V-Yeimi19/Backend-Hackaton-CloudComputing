import json
import os
import uuid
import hashlib
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

USUARIOS_TABLE = os.environ["USUARIOS_TABLE"]
TOKENS_TABLE = os.environ["TOKENS_TABLE"]

dynamodb = boto3.resource("dynamodb")
usuarios_table = dynamodb.Table(USUARIOS_TABLE)
tokens_table = dynamodb.Table(TOKENS_TABLE)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def lambda_handler(event, context):
    print("Event loginUsuario:", json.dumps(event))

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"message": "El body debe ser JSON"})

    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return _response(
            400,
            {"message": "Campos obligatorios: email, password"},
        )

    # Buscar usuario
    try:
        res = usuarios_table.get_item(Key={"email": email})
    except ClientError as e:
        print("Error leyendo tabla_usuarios:", e)
        return _response(500, {"message": "Error interno leyendo usuarios"})

    user = res.get("Item")
    if not user:
        return _response(401, {"message": "Credenciales inválidas"})

    password_hash = hash_password(password)
    if password_hash != user.get("passwordHash"):
        return _response(401, {"message": "Credenciales inválidas"})

    # Generar nuevo token de acceso
    now = datetime.utcnow().isoformat()
    token = str(uuid.uuid4())

    token_item = {
        "token": token,
        "email": email,
        "rol": user.get("rol"),
        "createdAt": now,
    }

    try:
        tokens_table.put_item(Item=token_item)
    except ClientError as e:
        print("Error guardando token:", e)
        return _response(500, {"message": "Error interno generando token"})

    return _response(
        200,
        {
            "message": "Login correcto",
            "token": token,
            "user": {
                "email": user.get("email"),
                "rol": user.get("rol"),
                "area": user.get("area"),
            },
        },
    )


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "body": json.dumps(body),
    }
