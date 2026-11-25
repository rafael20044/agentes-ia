"""Clase base abstracta para todos los agentes del sistema."""

from typing import Any

from communication.fipa_acl import BusMensajesFIPA
from environment.entorno_transcaribe import EntornoUrbanoTranscaribe


class AgenteBase:
    """Provee identidad, acceso al entorno y canal de comunicación FIPA-ACL."""

    nombre: str = "AgenteBase"

    def __init__(self, entorno: EntornoUrbanoTranscaribe, bus: BusMensajesFIPA):
        self.entorno = entorno
        self.bus = bus

    def enviar_mensaje(
        self,
        receiver: str,
        performative: str,
        protocol: str,
        instruccion: str,
    ) -> dict[str, Any]:
        return self.bus.emitir(
            sender=self.nombre,
            receiver=receiver,
            performative=performative,
            protocol=protocol,
            instruccion=instruccion,
        )
