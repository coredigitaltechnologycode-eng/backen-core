"""
main.py

Servidor FastAPI que expone el flujo de registro, login y endpoints
protegidos de administradores para que el frontend en Angular
pueda consumirlo.

Ejecutar:
    uvicorn main:app --reload --port 8000

Documentación interactiva (auto-generada):
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from firebase.nodos.admin_nodos import crear_admin, login_admin
from firebase.nodos.clientes_nodos import crear_cliente, login_cliente
from firebase.nodos.vender_nodo import crear_vendedor, login_vendedor
from seguridad.jwt_handler import crear_token
from seguridad.dependencias import obtener_admin_actual, obtener_cliente_actual

app = FastAPI(title="Backend Core API")

# --- CORS: permite que Angular (localhost:4200 en desarrollo) llame a esta API ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",   # Angular en desarrollo (ng serve)
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Esquemas de entrada ----------------------------------------------------

class RegistroAdminSchema(BaseModel):
    cedula: str
    nombres_completos: str
    rol: str
    correo: str
    contraseña: str


class LoginSchema(BaseModel):
    correo: str
    contraseña: str


class RegistroClienteSchema(BaseModel):
    cedula: str
    nombres_completos: str
    direccion: str
    correo: str
    telefono: str
    usuario_creado: str
    contraseña_creada: str
    plan_seleccionado: str


class LoginClienteSchema(BaseModel):
    identificador: str  # correo o usuario_creado
    contraseña: str


class RegistroVendedorSchema(BaseModel):
    # cedula_cliente NO va aquí: llega por la URL (path param), no por el body.
    cedula: str
    nombres_completos: str
    fecha_ingreso: str        # dd/mm/aaaa
    tipo_contrato: str        # tiempo_indefinido | plazo_fijo | temporal | practicas
    fecha_nacimiento: str     # dd/mm/aaaa
    salario: float
    usuario_creado: str
    contraseña_creada: str


class LoginVendedorSchema(BaseModel):
    # cedula_cliente NO va aquí: llega por la URL (path param), no por el body.
    usuario_creado: str
    contraseña: str


# --- Endpoints públicos ------------------------------------------------------

@app.get("/")
def ping():
    """Endpoint simple para comprobar que el servidor está vivo."""
    return {"status": "ok", "mensaje": "Backend Core corriendo correctamente"}


@app.post("/registro/admin")
def registrar_admin(datos: RegistroAdminSchema):
    """
    Recibe los datos del formulario desde Angular, los valida
    (registro/validacion_campos.py) y crea el nodo en Firebase
    (firebase/nodos/admin_nodos.py) con la contraseña cifrada.
    """
    resultado = crear_admin(datos.model_dump())

    if not resultado["exito"]:
        # 400 = error del cliente (datos inválidos o cédula duplicada)
        raise HTTPException(status_code=400, detail=resultado["errores"])

    return {"mensaje": "Administrador creado correctamente", "cedula": resultado["cedula"]}


@app.post("/login")
def login(datos: LoginSchema):
    """
    Valida credenciales (correo + contraseña) contra Firebase,
    y confirma que el rol del usuario sea "admin".
    Si son correctas, genera y retorna un token JWT que Angular
    debe guardar y enviar en futuras peticiones protegidas.

    Angular usa el campo "rol" de la respuesta para decidir
    a dónde redirigir tras el login.
    """
    resultado = login_admin(datos.correo, datos.contraseña)

    if not resultado["exito"]:
        # 401 = no autorizado (credenciales inválidas o rol no permitido)
        raise HTTPException(status_code=401, detail=resultado["error"])

    token = crear_token({
        "cedula": resultado["cedula"],
        "rol": resultado["rol"],
        "nombres_completos": resultado["nombres_completos"],
    })

    return {
        "mensaje": "Login exitoso",
        "token": token,
        "rol": resultado["rol"],
        "nombres_completos": resultado["nombres_completos"],
    }


# --- Endpoints públicos: clientes --------------------------------------------

@app.post("/registro/cliente")
def registrar_cliente(datos: RegistroClienteSchema):
    """
    Recibe los datos del formulario de ingreso de clientes desde Angular,
    los valida (registro/validacion_campos.py) y crea el nodo en Firebase
    (firebase/nodos/clientes_nodos.py) con la contraseña cifrada.
    """
    resultado = crear_cliente(datos.model_dump())

    if not resultado["exito"]:
        # 400 = error del cliente (datos inválidos o cédula/correo/usuario duplicado)
        raise HTTPException(status_code=400, detail=resultado["errores"])

    return {"mensaje": "Cliente registrado correctamente", "cedula": resultado["cedula"]}


@app.post("/login/cliente")
def login_cliente_endpoint(datos: LoginClienteSchema):
    """
    Valida credenciales (correo o usuario + contraseña) contra Firebase.
    Si son correctas, genera y retorna un token JWT con rol "cliente"
    que Angular debe guardar y enviar en futuras peticiones protegidas.
    """
    resultado = login_cliente(datos.identificador, datos.contraseña)

    if not resultado["exito"]:
        # 401 = no autorizado (credenciales inválidas)
        raise HTTPException(status_code=401, detail=resultado["error"])

    token = crear_token({
        "cedula": resultado["cedula"],
        "rol": resultado["rol"],
        "nombres_completos": resultado["nombres_completos"],
        "usuario_creado": resultado["usuario_creado"],
        "plan_seleccionado": resultado["plan_seleccionado"],
    })

    return {
        "mensaje": "Login exitoso",
        "token": token,
        "rol": resultado["rol"],
        "nombres_completos": resultado["nombres_completos"],
        "plan_seleccionado": resultado["plan_seleccionado"],
    }


# --- Endpoints públicos: colaboradores / vendedores --------------------------

@app.post("/clientes/{cedula_cliente}/colaboradores")
def registrar_vendedor(cedula_cliente: str, datos: RegistroVendedorSchema):
    """
    Recibe los datos del formulario de ingreso de vendedor/colaborador desde
    Angular, los valida (registro/validacion_campos.py) y crea el nodo
    anidado dentro del cliente dueño en Firebase (firebase/nodos/vender_nodo.py)
    con la contraseña cifrada.
    """
    resultado = crear_vendedor(cedula_cliente, datos.model_dump())

    if not resultado["exito"]:
        # 400 = error del cliente (datos inválidos, cliente inexistente o cédula/usuario duplicado)
        raise HTTPException(status_code=400, detail=resultado["errores"])

    return {"mensaje": "Colaborador registrado correctamente", "cedula": resultado["cedula"]}


@app.post("/clientes/{cedula_cliente}/colaboradores/login")
def login_vendedor_endpoint(cedula_cliente: str, datos: LoginVendedorSchema):
    """
    Valida credenciales (usuario + contraseña) del colaborador contra los
    colaboradores anidados en el cliente indicado. Si son correctas, genera
    y retorna un token JWT con rol "vendedor".
    """
    resultado = login_vendedor(cedula_cliente, datos.usuario_creado, datos.contraseña)

    if not resultado["exito"]:
        # 401 = no autorizado (credenciales inválidas)
        raise HTTPException(status_code=401, detail=resultado["error"])

    token = crear_token({
        "cedula": resultado["cedula"],
        "rol": resultado["rol"],
        "nombres_completos": resultado["nombres_completos"],
        "usuario_creado": resultado["usuario_creado"],
        "cedula_cliente": cedula_cliente,
    })

    return {
        "mensaje": "Login exitoso",
        "token": token,
        "rol": resultado["rol"],
        "nombres_completos": resultado["nombres_completos"],
    }


# --- Endpoints protegidos (requieren token JWT válido con rol "admin") -------
@app.get("/admin/dashboard")
def dashboard(admin_actual: dict = Depends(obtener_admin_actual)):
    """
    Endpoint protegido: solo responde si el token es válido,
    no ha expirado, y el rol dentro del token es "admin".

    FastAPI ejecuta obtener_admin_actual() antes de entrar aquí;
    si algo falla, ni siquiera llega a este código.
    """
    return {
        "mensaje": f"Bienvenido {admin_actual['nombres_completos']}",
        "rol": admin_actual["rol"],
        "cedula": admin_actual["cedula"],
    }


@app.get("/clientes/dashboard")
def dashboard_cliente(cliente_actual: dict = Depends(obtener_cliente_actual)):
    """
    Endpoint protegido: solo responde si el token es válido,
    no ha expirado, y el rol dentro del token es "cliente".

    FastAPI ejecuta obtener_cliente_actual() antes de entrar aquí;
    si algo falla, ni siquiera llega a este código.
    """
    return {
        "mensaje": f"Bienvenido {cliente_actual['nombres_completos']}",
        "rol": cliente_actual["rol"],
        "cedula": cliente_actual["cedula"],
        "plan_seleccionado": cliente_actual.get("plan_seleccionado"),
    }