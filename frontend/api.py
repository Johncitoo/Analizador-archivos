"""Cliente de la API REST del backend. Todas las llamadas HTTP pasan por aquí."""

import os

import requests

API_URL = os.environ.get("API_URL", "http://localhost:8000/api").rstrip("/")
TIMEOUT = 30  # segundos


class ErrorAPI(Exception):
    """Error al comunicarse con el backend, con un mensaje listo para mostrar."""


def _procesar(respuesta: requests.Response):
    if respuesta.ok:
        return respuesta.json()
    try:
        detalle = respuesta.json()
    except ValueError:
        detalle = respuesta.text
    if isinstance(detalle, dict):
        # DRF responde errores como {"campo": ["mensaje", ...]}
        detalle = " ".join(
            " ".join(map(str, v)) if isinstance(v, list) else str(v) for v in detalle.values()
        )
    raise ErrorAPI(f"Error {respuesta.status_code}: {detalle}")


def _llamar(metodo: str, ruta: str, **kwargs):
    try:
        respuesta = requests.request(metodo, f"{API_URL}{ruta}", timeout=TIMEOUT, **kwargs)
    except requests.RequestException as error:
        raise ErrorAPI(f"No se pudo conectar con el backend ({API_URL}).") from error
    return _procesar(respuesta)


def subir_archivo(nombre: str, contenido: bytes) -> dict:
    return _llamar("POST", "/archivos/", files={"archivo": (nombre, contenido)})


def listar_archivos() -> list[dict]:
    return _llamar("GET", "/archivos/")


def obtener_estadisticas() -> dict:
    return _llamar("GET", "/archivos/estadisticas/")
