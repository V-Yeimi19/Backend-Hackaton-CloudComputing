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

VALID_ROLES = {"administrativo", "usuario"}


def hash_password(password: str) -> str:
    # Simple para el reto (NO usar así en prod real)
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def lambda_handler(event, context):
    print("Event crearUsuario:", json.dumps(event))

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"message": "El body debe ser JSON"})

    email = body.get("email")
    password = body.get("password")
    rol = body.get("rol")
    area = body.get("area")

    if not email or not password or not rol or not area:
        return _response(
            400,
            {"message": "Campos obligatorios: email, password, rol, area"},
        )

    if rol not in VALID_ROLES:
        return _response(
            400,
            {"message": "Rol inválido, use 'administrativo' o 'usuario'"},
        )

    if "@" not in email:
        return _response(400, {"message": "Email inválido"})

    # ¿Ya existe?
    try:
        existing = usuarios_table.get_item(Key={"email": email})
    except ClientError as e:
        print("Error leyendo tabla_usuarios:", e)
        return _response(500, {"message": "Error interno leyendo usuarios"})

    if "Item" in existing:
        return _response(409, {"message": "El usuario ya existe"})

    now = datetime.utcnow().isoformat()
    password_hash = hash_password(password)

    user_item = {
        "email": email,
        "passwordHash": password_hash,
        "rol": rol,
        "area": area,
        "createdAt": now,
    }

    try:
        usuarios_table.put_item(Item=user_item)
    except ClientError as e:
        print("Error guardando usuario:", e)
        return _response(500, {"message": "Error interno guardando usuario"})

    # Generar token inicial al crear usuario (para tu flujo posterior)
    token = str(uuid.uuid4())
    token_item = {
        "token": token,
        "email": email,
        "rol": rol,
        "createdAt": now,
    }

    try:
        tokens_table.put_item(Item=token_item)
    except ClientError as e:
        print("Error guardando token:", e)
        return _response(500, {"message": "Error interno guardando token"})

    return _response(
        201,
        {
            "message": "Usuario creado correctamente",
            "token": token,
            "user": {
                "email": email,
                "rol": rol,
                "area": area,
                "createdAt": now,
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
