"""
conexion_dataset.py

Centraliza la conexión a Firebase Realtime Database.
Las credenciales NUNCA van hardcodeadas: se leen desde variables
de entorno definidas en el archivo .env (raíz del proyecto BACKEN-CORE).

Variables requeridas en .env:
    FIREBASE_CREDENTIALS_PATH=security/serviceAccountKey.json
    FIREBASE_DATABASE_URL=https://tu-proyecto-default-rtdb.firebaseio.com
"""

import os
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

# Carga las variables definidas en .env al entorno del proceso
load_dotenv()

_app = None  # Referencia única a la app de Firebase (patrón singleton)


def obtener_conexion():
    """
    Inicializa (una sola vez) la conexión con Firebase usando el
    service account indicado en FIREBASE_CREDENTIALS_PATH.

    Retorna la instancia de la app de Firebase ya inicializada.
    """
    global _app

    if _app is not None:
        return _app

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    database_url = os.getenv("FIREBASE_DATABASE_URL")

    if not cred_path:
        raise EnvironmentError(
            "Falta FIREBASE_CREDENTIALS_PATH en el archivo .env"
        )
    if not database_url:
        raise EnvironmentError(
            "Falta FIREBASE_DATABASE_URL en el archivo .env"
        )
    if not os.path.exists(cred_path):
        raise FileNotFoundError(
            f"No se encontró el archivo de credenciales en: {cred_path}"
        )

    cred = credentials.Certificate(cred_path)
    _app = firebase_admin.initialize_app(cred, {"databaseURL": database_url})
    return _app


def obtener_referencia(ruta: str = "/"):
    """
    Retorna una referencia a un nodo específico de la Realtime Database.

    Ejemplo:
        ref = obtener_referencia("admin_creados/0102030405")
        ref.set({...})
    """
    obtener_conexion()
    return db.reference(ruta)