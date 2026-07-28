"""
jwt_handler.py

Genera y valida tokens JWT para las sesiones de administradores.
La SECRET_KEY se lee desde .env, nunca hardcodeada.
"""

import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
EXPIRACION_MINUTOS = 60  # duración del token de sesión

if not SECRET_KEY:
    raise EnvironmentError("Falta JWT_SECRET_KEY en el archivo .env")


def crear_token(datos: dict) -> str:
    """Genera un JWT firmado con los datos del admin autenticado."""
    payload = datos.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=EXPIRACION_MINUTOS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str) -> dict | None:
    """Decodifica y valida un token. Retorna el payload o None si es inválido/expiró."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None