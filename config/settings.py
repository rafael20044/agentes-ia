"""Configuración centralizada y carga de variables de entorno."""

from dotenv import load_dotenv

load_dotenv()

ONTOLOGY = "Transcaribe"
# Temperatura baja para respuestas deterministas y estructura JSON estable
TEMPERATURE = 0.1
MAX_REINTENTOS = 3
ESPERA_BASE_SEG = 2.0

# Lista de modelos para hacer fallback si uno agota su cuota diaria
MODELOS_RESPALDO = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
]

# Lenguaje del contenido de los mensajes FIPA-ACL (texto natural en español)
LANGUAGE = "es"

# Reglas de decisión del Regulador (meta: mantener el intervalo de paso dentro de la tolerancia)
INTERVALO_MIN_KM = 0.30          # Por debajo: riesgo de agrupamiento, hay que frenar al bus de atrás
INTERVALO_MAX_KM = 0.80          # Por encima: hueco largo, el bus de atrás debe acelerar
VELOCIDAD_REGULACION_KMH = 30    # Velocidad objetivo cuando se frena al bus de atrás
VELOCIDAD_MAXIMA_PERMITIDA_KMH = 50  # Velocidad objetivo cuando debe recuperar el intervalo
TIEMPO_RETENCION_SEG = 45        # Retención en estación cuando el intervalo es demasiado corto
