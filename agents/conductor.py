"""Agente Conductor."""

from typing import Any

from agents.base_agent import AgenteBase
from communication.fipa_acl import Performativa, ProtocoloFIPA


class AgenteConductor(AgenteBase):
    nombre = "AgenteConductor"

    def aceptar_recorrido(self, bus_id: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteUnidadVehicular",
            performative=Performativa.AGREE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Acepta iniciar el recorrido en {bus_id}.",
        )

    def ejecutar_desplazamiento(self, bus_id: str, estacion: str) -> dict[str, Any]:
        self.entorno.desplazamiento_hacia_estacion(bus_id, estacion)
        return self.enviar_mensaje(
            receiver="AgenteUnidadVehicular",
            performative=Performativa.INFORM_DONE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Informa desplazamiento iniciado de {bus_id} hacia {estacion}.",
        )

    def aceptar_maniobra_regulacion(self, bus_id: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteUnidadVehicular",
            performative=Performativa.AGREE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Confirma que la maniobra es segura y la acepta para {bus_id}.",
        )

    def ejecutar_retencion_y_velocidad(
        self, bus_id: str, tiempo_retencion: int, velocidad_objetivo: int
    ) -> dict[str, Any]:
        self.entorno.retener_bus_y_ajustar_velocidad(
            bus_id, tiempo_retencion, velocidad_objetivo
        )
        return self.enviar_mensaje(
            receiver="AgenteUnidadVehicular",
            performative=Performativa.INFORM_DONE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Informa retención y ajuste de velocidad completados en {bus_id}.",
        )
