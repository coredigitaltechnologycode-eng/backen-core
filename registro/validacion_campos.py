"""
validacion_campos.py

Valida los datos de los formularios de registro (administradores y
clientes) ANTES de que lleguen a firebase/nodos/*.py.

Reglas aplicadas (administradores):
- cedula: exactamente 10 dígitos numéricos.
- nombres_completos: solo letras (con tildes/ñ) y espacios, mínimo 3 caracteres.
- rol: solo se acepta "admin" (valor fijo).
- correo: formato de correo electrónico válido.
- contraseña: mínimo 8 caracteres, al menos 1 mayúscula, 1 minúscula,
  1 número y 1 carácter especial.

Reglas aplicadas (clientes):
- cedula: exactamente 10 dígitos numéricos.
- nombres_completos: solo letras (con tildes/ñ) y espacios, mínimo 3 caracteres.
- direccion: mínimo 5 caracteres, texto libre.
- correo: formato de correo electrónico válido.
- telefono: exactamente 10 dígitos numéricos.
- usuario_creado: 4-30 caracteres alfanuméricos (guiones bajos y puntos permitidos).
- contraseña_creada: mismas reglas que la de administrador.
- plan_seleccionado: solo "basic", "pro" o "enterprise".
"""

import re

# --- Constantes de validación -------------------------------------------------

ROLES_PERMITIDOS = {"admin"}
PLANES_PERMITIDOS = {"basic", "pro", "enterprise"}

REGEX_CEDULA = re.compile(r"^\d{10}$")
REGEX_NOMBRES = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]{3,100}$")
REGEX_CORREO = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
REGEX_TELEFONO = re.compile(r"^\d{10}$")
REGEX_USUARIO = re.compile(r"^[A-Za-z0-9._]{4,30}$")
# Mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número, 1 carácter especial
REGEX_PASSWORD = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$"
)

CAMPOS_REQUERIDOS = ("cedula", "nombres_completos", "rol", "correo", "contraseña")

CAMPOS_REQUERIDOS_CLIENTE = (
    "cedula",
    "nombres_completos",
    "direccion",
    "correo",
    "telefono",
    "usuario_creado",
    "contraseña_creada",
    "plan_seleccionado",
)


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


def validar_direccion(direccion: str) -> bool:
    """Verifica que la dirección tenga al menos 5 caracteres."""
    if not isinstance(direccion, str):
        return False
    return len(direccion.strip()) >= 5


def validar_telefono(telefono: str) -> bool:
    """Verifica que el teléfono tenga exactamente 10 dígitos numéricos."""
    if not isinstance(telefono, str):
        return False
    return bool(REGEX_TELEFONO.match(telefono.strip()))


def validar_usuario(usuario: str) -> bool:
    """Verifica que el usuario tenga entre 4 y 30 caracteres alfanuméricos."""
    if not isinstance(usuario, str):
        return False
    return bool(REGEX_USUARIO.match(usuario.strip()))


def validar_plan(plan: str) -> bool:
    """Solo se permiten los planes: basic, pro, enterprise."""
    if not isinstance(plan, str):
        return False
    return plan.strip().lower() in PLANES_PERMITIDOS


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


# --- Validación completa del formulario de cliente -------------------------------

def validar_formulario_cliente(datos: dict) -> tuple[bool, dict]:
    """
    Valida todos los campos del formulario de registro de cliente.

    Parámetros
    ----------
    datos : dict
        Debe contener: cedula, nombres_completos, direccion, correo,
        telefono, usuario_creado, contraseña_creada, plan_seleccionado.

    Retorna
    -------
    (es_valido, errores) : tuple[bool, dict]
        es_valido es True solo si no hay ningún error.
        errores es un diccionario {campo: mensaje}.
    """
    errores = {}

    # 1. Verificar que no falten campos
    for campo in CAMPOS_REQUERIDOS_CLIENTE:
        if campo not in datos or datos[campo] in (None, ""):
            errores[campo] = "Este campo es obligatorio."

    if errores:
        return False, errores

    # 2. Validar cada campo individualmente
    if not validar_cedula(datos["cedula"]):
        errores["cedula"] = "La cédula debe tener exactamente 10 dígitos numéricos."

    if not validar_nombres(datos["nombres_completos"]):
        errores["nombres_completos"] = "El nombre solo puede contener letras y espacios (mínimo 3 caracteres)."

    if not validar_direccion(datos["direccion"]):
        errores["direccion"] = "La dirección debe tener al menos 5 caracteres."

    if not validar_correo(datos["correo"]):
        errores["correo"] = "El correo electrónico no tiene un formato válido."

    if not validar_telefono(datos["telefono"]):
        errores["telefono"] = "El teléfono debe tener exactamente 10 dígitos numéricos."

    if not validar_usuario(datos["usuario_creado"]):
        errores["usuario_creado"] = "El usuario debe tener entre 4 y 30 caracteres (letras, números, '.' o '_')."

    if not validar_contraseña(datos["contraseña_creada"]):
        errores["contraseña_creada"] = (
            "La contraseña debe tener mínimo 8 caracteres, incluir al menos "
            "una mayúscula, una minúscula, un número y un carácter especial."
        )

    if not validar_plan(datos["plan_seleccionado"]):
        errores["plan_seleccionado"] = "Plan no permitido. Valores válidos: 'basic', 'pro', 'enterprise'."

    es_valido = len(errores) == 0
    return es_valido, errores