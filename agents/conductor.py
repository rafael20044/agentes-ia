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
        # Acciona el movimiento físico del bus en el entorno y confirma con INFORM-DONE
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

    def ejecutar_ajuste(self, bus_id: str, decision: dict[str, Any]) -> dict[str, Any]:
        # El conductor es quien mueve el bus: ejecuta la orden sobre el entorno y confirma
        if decision["accion"] == "bajar":
            self.entorno.retener_bus_y_ajustar_velocidad(
                bus_id, decision["tiempo_retencion"], decision["velocidad_objetivo"]
            )
            hecho = (
                f"se detuvo {decision['tiempo_retencion']}s en la estación y bajó la velocidad "
                f"a {decision['velocidad_objetivo']} km/h"
            )
        else:
            self.entorno.ajustar_velocidad(bus_id, decision["velocidad_objetivo"])
            hecho = f"subió la velocidad a {decision['velocidad_objetivo']} km/h"
        return self.enviar_mensaje(
            receiver="AgenteUnidadVehicular",
            performative=Performativa.INFORM_DONE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Informa que {bus_id} {hecho}.",
        )
