"""
admin_nodos.py

Construye el nodo 'admin_creados' en Firebase Realtime Database.

Estructura resultante:

admin_creados/
    <cedula>/
        cedula
        nombres_completos
        rol
        correo
        contraseña   (hash bcrypt, nunca texto plano)

Flujo esperado:
    1. registro/validacion_campos.py valida los datos del formulario.
    2. Si son válidos, este módulo cifra la contraseña y crea el nodo.
    3. Para login: se busca por correo, se verifica la contraseña
    y se confirma que el rol sea "admin".
"""

import bcrypt

from firebase.conexion_dataset import obtener_referencia
from registro.validacion_campos import validar_formulario_admin

NODO_ADMIN = "admin_creados"


# --- Utilidades de cifrado ------------------------------------------------

def _cifrar_contraseña(contraseña: str) -> str:
    """Genera el hash bcrypt de la contraseña (incluye salt aleatorio)."""
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(contraseña.encode("utf-8"), salt)
    return hash_bytes.decode("utf-8")


def verificar_contraseña(contraseña_plana: str, hash_guardado: str) -> bool:
    """
    Útil para el login: compara una contraseña en texto plano
    contra el hash guardado en Firebase.
    """
    return bcrypt.checkpw(
        contraseña_plana.encode("utf-8"),
        hash_guardado.encode("utf-8"),
    )


# --- Creación del nodo -----------------------------------------------------

def crear_admin(datos: dict) -> dict:
    """
    Valida y crea un administrador en el nodo 'admin_creados'.

    Parámetros
    ----------
    datos : dict
        {
            "cedula": "0102030405",
            "nombres_completos": "Juan Pérez",
            "rol": "admin",
            "correo": "juan@correo.com",
            "contraseña": "Clave123!"
        }

    Retorna
    -------
    dict con:
        {"exito": True, "cedula": "..."}                si todo salió bien
        {"exito": False, "errores": {...}}               si hubo error de validación
                                                        o la cédula ya existe
    """
    # 1. Validar el formulario (seguridad de entrada)
    es_valido, errores = validar_formulario_admin(datos)
    if not es_valido:
        return {"exito": False, "errores": errores}

    cedula = datos["cedula"].strip()
    ref = obtener_referencia(f"{NODO_ADMIN}/{cedula}")

    # 2. Evitar administradores duplicados por cédula
    if ref.get() is not None:
        return {
            "exito": False,
            "errores": {"cedula": "Ya existe un administrador registrado con esta cédula."},
        }

    # 3. Cifrar contraseña antes de guardar
    nuevo_admin = {
        "cedula": cedula,
        "nombres_completos": datos["nombres_completos"].strip(),
        "rol": datos["rol"].strip().lower(),
        "correo": datos["correo"].strip().lower(),
        "contraseña": _cifrar_contraseña(datos["contraseña"]),
    }

    # 4. Guardar el nodo en Firebase
    ref.set(nuevo_admin)

    return {"exito": True, "cedula": cedula}


# --- Login -------------------------------------------------------------

def buscar_admin_por_correo(correo: str) -> dict | None:
    """
    Busca un admin por correo dentro del nodo admin_creados.
    Firebase RTDB no permite queries directas por campo anidado
    en este esquema, así que se recorre el nodo completo.

    Retorna el dict del admin (incluye cedula) o None si no existe.
    """
    ref = obtener_referencia(NODO_ADMIN)
    todos = ref.get()  # dict {cedula: {...}} o None si el nodo está vacío

    if not todos:
        return None

    correo = correo.strip().lower()
    for cedula, datos in todos.items():
        if datos.get("correo") == correo:
            datos["cedula"] = cedula  # aseguramos que venga incluida
            return datos

    return None


def login_admin(correo: str, contraseña: str) -> dict:
    """
    Valida credenciales de un administrador y confirma que su rol
    sea "admin" antes de autorizar el acceso.

    Retorna:
        {"exito": True, "cedula": ..., "nombres_completos": ..., "rol": ...}
        {"exito": False, "error": "..."}
    """
    admin = buscar_admin_por_correo(correo)

    if admin is None:
        return {"exito": False, "error": "Credenciales inválidas."}

    if not verificar_contraseña(contraseña, admin["contraseña"]):
        return {"exito": False, "error": "Credenciales inválidas."}

    # --- Verificación explícita de rol ---
    if admin.get("rol") != "admin":
        return {"exito": False, "error": "No tienes permisos para acceder a este panel."}

    return {
        "exito": True,
        "cedula": admin["cedula"],
        "nombres_completos": admin["nombres_completos"],
        "rol": admin["rol"],
    }