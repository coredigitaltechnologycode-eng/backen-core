"""
clientes_nodos.py

Construye el nodo 'Clientes_Registrados' en Firebase Realtime Database.

Estructura resultante:

Clientes_Registrados/
    <cedula>/
        Cedula
        Nombres_Completos
        Direccion
        Correo_Electronico
        Telefono
        Usuario_Creado
        Contraseña_Creada   (hash bcrypt, nunca texto plano)
        Plan_Seleccionado

Flujo esperado:
    1. registro/validacion_campos.py valida los datos del formulario
       (validar_formulario_cliente).
    2. Si son válidos, este módulo cifra la contraseña y crea el nodo.
    3. Para login: se busca por correo o usuario, se verifica la
       contraseña y se retorna la sesión del cliente.
"""

import bcrypt

from firebase.conexion_dataset import obtener_referencia
from registro.validacion_campos import validar_formulario_cliente

NODO_CLIENTE = "Clientes_Registrados"


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

def crear_cliente(datos: dict) -> dict:
    """
    Valida y crea un cliente en el nodo 'Clientes_Registrados'.

    Parámetros
    ----------
    datos : dict
        {
            "cedula": "0102030405",
            "nombres_completos": "Juan Gabriel García López",
            "direccion": "Av. 12 de Octubre N24-11 y Fco. de Orellana, Quito",
            "correo": "juan@correo.com",
            "telefono": "0991234567",
            "usuario_creado": "jgarcia",
            "contraseña_creada": "Clave123!",
            "plan_seleccionado": "pro"
        }

    Retorna
    -------
    dict con:
        {"exito": True, "cedula": "..."}                si todo salió bien
        {"exito": False, "errores": {...}}               si hubo error de validación
                                                        o la cédula/usuario/correo ya existe
    """
    # 1. Validar el formulario (seguridad de entrada)
    es_valido, errores = validar_formulario_cliente(datos)
    if not es_valido:
        return {"exito": False, "errores": errores}

    cedula = datos["cedula"].strip()
    correo = datos["correo"].strip().lower()
    usuario = datos["usuario_creado"].strip()

    ref = obtener_referencia(f"{NODO_CLIENTE}/{cedula}")

    # 2. Evitar clientes duplicados por cédula
    if ref.get() is not None:
        return {
            "exito": False,
            "errores": {"cedula": "Ya existe un cliente registrado con esta cédula."},
        }

    # 3. Evitar correo y usuario duplicados dentro del nodo completo
    if buscar_cliente_por_correo(correo) is not None:
        return {
            "exito": False,
            "errores": {"correo": "Ya existe un cliente registrado con este correo."},
        }

    if buscar_cliente_por_usuario(usuario) is not None:
        return {
            "exito": False,
            "errores": {"usuario_creado": "Este nombre de usuario ya está en uso."},
        }

    # 4. Cifrar contraseña antes de guardar
    nuevo_cliente = {
        "Cedula": cedula,
        "Nombres_Completos": datos["nombres_completos"].strip(),
        "Direccion": datos["direccion"].strip(),
        "Correo_Electronico": correo,
        "Telefono": datos["telefono"].strip(),
        "Usuario_Creado": usuario,
        "Contraseña_Creada": _cifrar_contraseña(datos["contraseña_creada"]),
        "Plan_Seleccionado": datos["plan_seleccionado"].strip().lower(),
    }

    # 5. Guardar el nodo en Firebase
    ref.set(nuevo_cliente)

    return {"exito": True, "cedula": cedula}


# --- Búsquedas -------------------------------------------------------------

def _obtener_todos_los_clientes() -> dict:
    """Retorna el dict completo {cedula: {...}} del nodo, o {} si está vacío."""
    ref = obtener_referencia(NODO_CLIENTE)
    todos = ref.get()
    return todos or {}


def buscar_cliente_por_correo(correo: str) -> dict | None:
    """
    Busca un cliente por correo dentro del nodo Clientes_Registrados.
    Firebase RTDB no permite queries directas por campo anidado
    en este esquema, así que se recorre el nodo completo.

    Retorna el dict del cliente (incluye Cedula) o None si no existe.
    """
    correo = correo.strip().lower()
    for cedula, datos in _obtener_todos_los_clientes().items():
        if datos.get("Correo_Electronico") == correo:
            datos["Cedula"] = cedula
            return datos
    return None


def buscar_cliente_por_usuario(usuario: str) -> dict | None:
    """
    Busca un cliente por su Usuario_Creado dentro del nodo Clientes_Registrados.

    Retorna el dict del cliente (incluye Cedula) o None si no existe.
    """
    usuario = usuario.strip()
    for cedula, datos in _obtener_todos_los_clientes().items():
        if datos.get("Usuario_Creado") == usuario:
            datos["Cedula"] = cedula
            return datos
    return None


# --- Login -------------------------------------------------------------

def login_cliente(identificador: str, contraseña: str) -> dict:
    """
    Valida credenciales de un cliente y autoriza el acceso.

    El identificador puede ser el correo o el usuario creado, para
    darle flexibilidad al formulario de login del frontend.

    Retorna:
        {
            "exito": True,
            "cedula": ...,
            "nombres_completos": ...,
            "usuario_creado": ...,
            "plan_seleccionado": ...,
            "rol": "cliente",
        }
        {"exito": False, "error": "..."}
    """
    identificador = identificador.strip()

    cliente = buscar_cliente_por_correo(identificador.lower())
    if cliente is None:
        cliente = buscar_cliente_por_usuario(identificador)

    if cliente is None:
        return {"exito": False, "error": "Credenciales inválidas."}

    if not verificar_contraseña(contraseña, cliente["Contraseña_Creada"]):
        return {"exito": False, "error": "Credenciales inválidas."}

    return {
        "exito": True,
        "cedula": cliente["Cedula"],
        "nombres_completos": cliente["Nombres_Completos"],
        "usuario_creado": cliente["Usuario_Creado"],
        "plan_seleccionado": cliente["Plan_Seleccionado"],
        "rol": "cliente",
    }
