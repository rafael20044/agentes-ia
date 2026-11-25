"""Configuración centralizada y carga de variables de entorno."""

from dotenv import load_dotenv

load_dotenv()

ONTOLOGY = "Transcaribe"
TEMPERATURE = 0.1
MAX_REINTENTOS = 3
ESPERA_BASE_SEG = 2.0

MODELOS_RESPALDO = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
]
