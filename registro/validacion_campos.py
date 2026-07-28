"""
validacion_campos.py

Valida los datos del formulario de registro de administradores
ANTES de que lleguen a firebase/nodos/admin_nodos.py.

Reglas aplicadas:
- cedula: exactamente 10 dígitos numéricos.
- nombres_completos: solo letras (con tildes/ñ) y espacios, mínimo 3 caracteres.
- rol: solo se acepta "admin" (valor fijo).
- correo: formato de correo electrónico válido.
- contraseña: mínimo 8 caracteres, al menos 1 mayúscula, 1 minúscula,
  1 número y 1 carácter especial.
"""

import re

# --- Constantes de validación -------------------------------------------------

ROLES_PERMITIDOS = {"admin"}

REGEX_CEDULA = re.compile(r"^\d{10}$")
REGEX_NOMBRES = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]{3,100}$")
REGEX_CORREO = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
# Mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número, 1 carácter especial
REGEX_PASSWORD = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$"
)

CAMPOS_REQUERIDOS = ("cedula", "nombres_completos", "rol", "correo", "contraseña")


# --- Validadores individuales --------------------------------------------------

def validar_cedula(cedula: str) -> bool:
    """Verifica que la cédula tenga exactamente 10 dígitos numéricos."""
    if not isinstance(cedula, str):
        return False
    return bool(REGEX_CEDULA.match(cedula.strip()))


def validar_nombres(nombres: str) -> bool:
    """Verifica que el nombre solo contenga letras y espacios."""
    if not isinstance(nombres, str):
        return False
    return bool(REGEX_NOMBRES.match(nombres.strip()))


def validar_rol(rol: str) -> bool:
    """Solo se permite el rol 'admin'."""
    if not isinstance(rol, str):
        return False
    return rol.strip().lower() in ROLES_PERMITIDOS


def validar_correo(correo: str) -> bool:
    """Verifica formato de correo electrónico."""
    if not isinstance(correo, str):
        return False
    return bool(REGEX_CORREO.match(correo.strip()))


def validar_contraseña(contraseña: str) -> bool:
    """
    Exige mínimo 8 caracteres, con mayúscula, minúscula, número
    y carácter especial.
    """
    if not isinstance(contraseña, str):
        return False
    return bool(REGEX_PASSWORD.match(contraseña))


# --- Validación completa del formulario ----------------------------------------

def validar_formulario_admin(datos: dict) -> tuple[bool, dict]:
    """
    Valida todos los campos del formulario de registro de administrador.

    Parámetros
    ----------
    datos : dict
        Debe contener: cedula, nombres_completos, rol, correo, contraseña.

    Retorna
    -------
    (es_valido, errores) : tuple[bool, dict]
        es_valido es True solo si no hay ningún error.
        errores es un diccionario {campo: mensaje}.
    """
    errores = {}

    # 1. Verificar que no falten campos
    for campo in CAMPOS_REQUERIDOS:
        if campo not in datos or datos[campo] in (None, ""):
            errores[campo] = "Este campo es obligatorio."

    if errores:
        return False, errores

    # 2. Validar cada campo individualmente
    if not validar_cedula(datos["cedula"]):
        errores["cedula"] = "La cédula debe tener exactamente 10 dígitos numéricos."

    if not validar_nombres(datos["nombres_completos"]):
        errores["nombres_completos"] = "El nombre solo puede contener letras y espacios (mínimo 3 caracteres)."

    if not validar_rol(datos["rol"]):
        errores["rol"] = "Rol no permitido. Único valor válido: 'admin'."

    if not validar_correo(datos["correo"]):
        errores["correo"] = "El correo electrónico no tiene un formato válido."

    if not validar_contraseña(datos["contraseña"]):
        errores["contraseña"] = (
            "La contraseña debe tener mínimo 8 caracteres, incluir al menos "
            "una mayúscula, una minúscula, un número y un carácter especial."
        )

    es_valido = len(errores) == 0
    return es_valido, errores