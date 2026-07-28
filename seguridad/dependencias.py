"""
dependencias.py

Dependencia de FastAPI para proteger endpoints con JWT.
Valida que el token sea correcto Y que el rol sea "admin".
Se agrega como parámetro en cualquier ruta que requiera login.
"""

from fastapi import Header, HTTPException
from seguridad.jwt_handler import verificar_token


def obtener_admin_actual(authorization: str = Header(None)) -> dict:
    """
    Extrae y valida el token del header Authorization.
    Formato esperado: "Bearer <token>"

    Verifica:
        1. Que el header exista y tenga el formato correcto.
        2. Que el token sea válido (firma correcta y no expirado).
        3. Que el rol dentro del token sea "admin".

    Retorna el payload del token (cedula, rol, nombres_completos)
    si todo es válido, o lanza HTTPException en caso contrario.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado.")

    token = authorization.split(" ")[1]
    payload = verificar_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    if payload.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador.")

    return payload