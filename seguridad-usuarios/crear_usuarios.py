import json
import os
import uuid
import hashlib
import boto3
import traceback
from datetime import datetime
from botocore.exceptions import ClientError

VALID_ROLES = {"administrativo", "usuario"}


def hash_password(password: str) -> str:
    # Simple para el reto (NO usar así en prod real)
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def lambda_handler(event, context):
    print("Event crearUsuario:", json.dumps(event))

    try:
        usuarios_table_name = os.environ.get("USUARIOS_TABLE")
        tokens_table_name = os.environ.get("TOKENS_TABLE")

        if not usuarios_table_name or not tokens_table_name:
            raise RuntimeError(
                f"Faltan variables de entorno: "
                f"USUARIOS_TABLE={usuarios_table_name}, "
                f"TOKENS_TABLE={tokens_table_name}"
            )

        dynamodb = boto3.resource("dynamodb")
        usuarios_table = dynamodb.Table(usuarios_table_name)
        tokens_table = dynamodb.Table(tokens_table_name)

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

        # Generar token inicial al crear usuario
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

    except Exception as e:
        # Cualquier error no controlado llega aquí
        print("ERROR NO CONTROLADO en crearUsuario:", str(e))
        print(traceback.format_exc())
        # Para desarrollo, devuelvo el detalle; en prod podrías ocultarlo
        return _response(
            500,
            {
                "message": "Error interno en crearUsuario",
                "detail": str(e),
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
