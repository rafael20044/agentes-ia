"""Cliente resiliente para Google GenAI con reintentos y respaldo de modelos."""

import json
import time
from typing import Any

from google import genai
from google.genai import errors, types

from config.settings import (
    ESPERA_BASE_SEG,
    MAX_REINTENTOS,
    MODELOS_RESPALDO,
    TEMPERATURE,
)


class GeminiLLMClient:
    """Encapsula la comunicación con la API de Gemini y maneja errores transitorios/cuota."""

    def __init__(
        self,
        modelos: list[str] | None = None,
        temperature: float = TEMPERATURE,
        max_reintentos: int = MAX_REINTENTOS,
        espera_base: float = ESPERA_BASE_SEG,
    ):
        # Desactivamos reintentos internos del SDK para controlar el backoff manualmente
        self._client = genai.Client(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1)
            )
        )
        self._modelos = list(modelos or MODELOS_RESPALDO)
        self._modelo_actual_idx = 0
        self._temperature = temperature
        self._max_reintentos = max_reintentos
        self._espera_base = espera_base

    def generar_json(self, system_prompt: str, instruccion: str) -> dict[str, Any]:
        """Solicita una respuesta JSON estructurada con reintentos y fallback automático."""
        ultimo_error: Exception | None = None

        while self._modelo_actual_idx < len(self._modelos):
            modelo = self._modelos[self._modelo_actual_idx]
            for intento in range(1, self._max_reintentos + 1):
                try:
                    # Forzamos salida en formato JSON puro con response_mime_type
                    response = self._client.models.generate_content(
                        model=modelo,
                        contents=instruccion,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                            temperature=self._temperature,
                        ),
                    )
                    return json.loads(response.text)
                except errors.APIError as e:
                    ultimo_error = e
                    es_cuota_diaria = e.code == 429 and (
                        "PerDay" in str(e) or "per day" in str(e).lower()
                    )
                    # Si el modelo no existe o agotó cuota diaria, pasamos al siguiente modelo
                    if e.code == 404 or es_cuota_diaria:
                        print(
                            f"   [API {e.code}] Modelo '{modelo}' sin cuota diaria o no disponible. "
                            "Probando siguiente modelo..."
                        )
                        break
                    # Backoff exponencial (2s, 4s) para errores temporales de red o rate limit por minuto
                    if e.code in (429, 500, 503, 504) and intento < self._max_reintentos:
                        espera = self._espera_base * (2 ** (intento - 1))
                        print(
                            f"   [API {e.code}] ({modelo}) Reintentando "
                            f"({intento}/{self._max_reintentos}) en {espera:.0f}s..."
                        )
                        time.sleep(espera)
                    elif e.code in (429, 500, 503, 504):
                        print(
                            f"   [API {e.code}] Modelo '{modelo}' falló tras {intento} intentos. "
                            "Probando siguiente modelo..."
                        )
                        break
                    else:
                        raise
            self._modelo_actual_idx += 1

        if ultimo_error is not None:
            raise ultimo_error
        raise RuntimeError("No hay modelos disponibles configurados en GeminiLLMClient.")
