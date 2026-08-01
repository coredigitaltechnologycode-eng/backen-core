"""
dependencias.py

Dependencias de FastAPI para proteger endpoints con JWT.
Validan que el token sea correcto Y que el rol coincida con el esperado
("admin" o "cliente"). Se agregan como parámetro en cualquier ruta que
requiera login.
"""

from fastapi import Header, HTTPException
from seguridad.jwt_handler import verificar_token


def _extraer_payload_validado(authorization: str | None) -> dict:
    """
    Extrae y valida el token del header Authorization.
    Formato esperado: "Bearer <token>"

    Verifica:
        1. Que el header exista y tenga el formato correcto.
        2. Que el token sea válido (firma correcta y no expirado).

    Retorna el payload del token, o lanza HTTPException en caso contrario.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado.")

    token = authorization.split(" ")[1]
    payload = verificar_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    return payload


def obtener_admin_actual(authorization: str = Header(None)) -> dict:
    """
    Valida el token y confirma que el rol dentro del token sea "admin".

    Retorna el payload del token (cedula, rol, nombres_completos)
    si todo es válido, o lanza HTTPException en caso contrario.
    """
    payload = _extraer_payload_validado(authorization)

    if payload.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="No tienes permisos de administrador.")

    return payload


def obtener_cliente_actual(authorization: str = Header(None)) -> dict:
    """
    Valida el token y confirma que el rol dentro del token sea "cliente".

    Retorna el payload del token (cedula, rol, nombres_completos,
    usuario_creado, plan_seleccionado) si todo es válido, o lanza
    HTTPException en caso contrario.
    """
    payload = _extraer_payload_validado(authorization)

    if payload.get("rol") != "cliente":
        raise HTTPException(status_code=403, detail="No tienes permisos de cliente.")

    return payload