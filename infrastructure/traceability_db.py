"""Base de datos en memoria para trazabilidad de mensajes FIPA-ACL."""

import json
from typing import Any


class BaseDatosTrazabilidad:
    """Registra y audita todos los mensajes FIPA-ACL intercambiados por los agentes."""

    def __init__(self):
        self._registros: list[dict[str, Any]] = []

    def registrar(self, msg: dict[str, Any]) -> None:
        self._registros.append(msg)
        print(
            f"[FIPA-ACL] {msg['sender']} -> {msg['receiver']} | "
            f"<<ACL:{msg['performative'].upper()}>>"
        )
        print(f"           Contenido: {json.dumps(msg['content'], ensure_ascii=False)}")

    @property
    def registros(self) -> list[dict[str, Any]]:
        return list(self._registros)

    def total(self) -> int:
        return len(self._registros)
