"""Base de datos con persistencia en JSON para trazabilidad de mensajes FIPA-ACL."""

from datetime import datetime
import json
from pathlib import Path
from typing import Any


class BaseDatosTrazabilidad:
    """Registra, audita y persiste en JSON todos los mensajes FIPA-ACL intercambiados."""

    def __init__(self, archivo_salida: str | Path = "trazabilidad_fipa.json"):
        self._registros: list[dict[str, Any]] = []
        self.ruta_archivo: Path = Path(archivo_salida).resolve()

    def registrar(self, msg: dict[str, Any]) -> None:
        # Agregamos marca de tiempo ISO 8601 antes de guardar el mensaje en disco
        registro = {
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            **msg,
        }
        self._registros.append(registro)
        self._guardar_json()
        print(
            f"[FIPA-ACL] ({registro['timestamp']}) {registro['sender']} -> {registro['receiver']} | "
            f"<<ACL:{registro['performative'].upper()}>>"
        )
        print(f"           Contenido: {registro['content']}")

    def _guardar_json(self) -> None:
        # Guardado automático en UTF-8 conservando tildes y formato legible
        self.ruta_archivo.write_text(
            json.dumps(self._registros, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def registros(self) -> list[dict[str, Any]]:
        return list(self._registros)

    def total(self) -> int:
        return len(self._registros)
