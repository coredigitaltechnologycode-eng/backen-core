"""
vender_nodo.py

Construye el nodo 'Colaboradores' (vendedores) DENTRO de cada cliente en
Firebase Realtime Database. Un colaborador siempre pertenece a un cliente,
nunca existe como nodo raíz independiente.

Estructura resultante:

Clientes_Registrados/
    <cedula_cliente>/
        ... (campos propios del cliente)
        Colaboradores/
            <cedula_colaborador>/
                Cedula
                Nombres_Completos
                Fecha_Ingreso
                Tipo_Contrato
                Fecha_Nacimiento
                Salario
                Usuario_Creado
                Contraseña_Creada   (hash bcrypt, nunca texto plano)

Flujo esperado:
    1. registro/validacion_campos.py valida los datos del formulario
    (validar_formulario_vendedor).
    2. Si son válidos, este módulo verifica que el cliente dueño exista,
    cifra la contraseña y crea el nodo anidado.
    3. Para login: se busca por usuario dentro de los colaboradores de
    ESE cliente, se verifica la contraseña y se retorna la sesión.
"""

import bcrypt

from firebase.conexion_dataset import obtener_referencia
from registro.validacion_campos import validar_formulario_vendedor

NODO_CLIENTES = "Clientes_Registrados"
NODO_COLABORADORES = "Colaboradores"


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

def crear_vendedor(cedula_cliente: str, datos: dict) -> dict:
    """
    Valida y crea un colaborador/vendedor dentro de un cliente ya existente.

    Parámetros
    ----------
    cedula_cliente : str
        Cédula del cliente dueño del negocio (nodo padre en
        Clientes_Registrados) al que pertenece este colaborador.
    datos : dict
        {
            "cedula": "0102030405",
            "nombres_completos": "Juan Gabriel García López",
            "fecha_ingreso": "15/10/2023",
            "tipo_contrato": "tiempo_indefinido",
            "fecha_nacimiento": "05/04/1990",
            "salario": 1200.00,
            "usuario_creado": "jgarcia123",
            "contraseña_creada": "Clave123!"
        }

    Retorna
    -------
    dict con:
        {"exito": True, "cedula": "..."}                si todo salió bien
        {"exito": False, "errores": {...}}               si hubo error de validación,
                                                        el cliente no existe, o la
                                                        cédula/usuario ya existe
    """
    # 1. Validar el formulario (seguridad de entrada)
    es_valido, errores = validar_formulario_vendedor(datos)
    if not es_valido:
        return {"exito": False, "errores": errores}

    cedula_cliente = cedula_cliente.strip()
    cedula_colaborador = datos["cedula"].strip()
    usuario = datos["usuario_creado"].strip()

    # 2. Confirmar que el cliente dueño existe antes de anidar el colaborador
    ref_cliente = obtener_referencia(f"{NODO_CLIENTES}/{cedula_cliente}")
    if ref_cliente.get() is None:
        return {
            "exito": False,
            "errores": {"cedula_cliente": "No existe un cliente registrado con esta cédula."},
        }

    ref_colaborador = obtener_referencia(
        f"{NODO_CLIENTES}/{cedula_cliente}/{NODO_COLABORADORES}/{cedula_colaborador}"
    )

    # 3. Evitar colaboradores duplicados por cédula dentro del mismo cliente
    if ref_colaborador.get() is not None:
        return {
            "exito": False,
            "errores": {"cedula": "Ya existe un colaborador registrado con esta cédula para este cliente."},
        }

    # 4. Evitar usuario duplicado dentro de los colaboradores de ese cliente
    if buscar_colaborador_por_usuario(cedula_cliente, usuario) is not None:
        return {
            "exito": False,
            "errores": {"usuario_creado": "Este nombre de usuario ya está en uso para este cliente."},
        }

    # 5. Cifrar contraseña antes de guardar
    nuevo_colaborador = {
        "Cedula": cedula_colaborador,
        "Nombres_Completos": datos["nombres_completos"].strip(),
        "Fecha_Ingreso": datos["fecha_ingreso"].strip(),
        "Tipo_Contrato": datos["tipo_contrato"].strip().lower(),
        "Fecha_Nacimiento": datos["fecha_nacimiento"].strip(),
        "Salario": float(datos["salario"]),
        "Usuario_Creado": usuario,
        "Contraseña_Creada": _cifrar_contraseña(datos["contraseña_creada"]),
    }

    # 6. Guardar el nodo anidado en Firebase
    ref_colaborador.set(nuevo_colaborador)

    return {"exito": True, "cedula": cedula_colaborador}


# --- Búsquedas -------------------------------------------------------------

def _obtener_colaboradores(cedula_cliente: str) -> dict:
    """Retorna el dict completo {cedula: {...}} de los colaboradores de un cliente, o {} si no hay."""
    ref = obtener_referencia(f"{NODO_CLIENTES}/{cedula_cliente.strip()}/{NODO_COLABORADORES}")
    todos = ref.get()
    return todos or {}


def buscar_colaborador_por_usuario(cedula_cliente: str, usuario: str) -> dict | None:
    """
    Busca un colaborador por su Usuario_Creado dentro de los colaboradores
    de un cliente específico.

    Retorna el dict del colaborador (incluye Cedula) o None si no existe.
    """
    usuario = usuario.strip()
    for cedula, datos in _obtener_colaboradores(cedula_cliente).items():
        if datos.get("Usuario_Creado") == usuario:
            datos["Cedula"] = cedula
            return datos
    return None


# --- Login -------------------------------------------------------------

def login_vendedor(cedula_cliente: str, usuario: str, contraseña: str) -> dict:
    """
    Valida credenciales de un colaborador dentro de un cliente específico
    y autoriza el acceso.

    Retorna:
        {
            "exito": True,
            "cedula": ...,
            "nombres_completos": ...,
            "usuario_creado": ...,
            "tipo_contrato": ...,
            "rol": "vendedor",
        }
        {"exito": False, "error": "..."}
    """
    colaborador = buscar_colaborador_por_usuario(cedula_cliente, usuario)

    if colaborador is None:
        return {"exito": False, "error": "Credenciales inválidas."}

    if not verificar_contraseña(contraseña, colaborador["Contraseña_Creada"]):
        return {"exito": False, "error": "Credenciales inválidas."}

    return {
        "exito": True,
        "cedula": colaborador["Cedula"],
        "nombres_completos": colaborador["Nombres_Completos"],
        "usuario_creado": colaborador["Usuario_Creado"],
        "tipo_contrato": colaborador["Tipo_Contrato"],
        "rol": "vendedor",
    }
