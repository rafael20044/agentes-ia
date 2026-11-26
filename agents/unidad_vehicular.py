"""Agente Unidad Vehicular."""

from typing import Any

from agents.base_agent import AgenteBase
from communication.fipa_acl import Performativa, ProtocoloFIPA


class AgenteUnidadVehicular(AgenteBase):
    nombre = "AgenteUnidadVehicular"

    def solicitar_inicio_recorrido_conductor(
        self, bus_id: str, estacion: str, ruta: str
    ) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteConductor",
            performative=Performativa.REQUEST,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Solicita iniciar recorrido de refuerzo en {bus_id} "
                f"hacia {estacion} (ruta {ruta})."
            ),
        )

    def confirmar_recorrido_aceptado(self, bus_id: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteReguladorRutaFrecuencias",
            performative=Performativa.AGREE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Confirma recorrido aceptado por el conductor de {bus_id}.",
        )

    def informar_unidad_en_ruta(self, bus_id: str, estacion: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteReguladorRutaFrecuencias",
            performative=Performativa.INFORM_DONE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Informa {bus_id} en ruta hacia {estacion}.",
        )

    def reportar_telemetria(self, bus_id: str, ruta: str) -> dict[str, Any]:
        # Lee GPS y velocidad del bus en el entorno para enviárselos al Regulador
        telemetria = self.entorno.consultar_telemetria_bus(bus_id)
        return self.enviar_mensaje(
            receiver="AgenteReguladorRutaFrecuencias",
            performative=Performativa.INFORM,
            protocol=ProtocoloFIPA.INFORM,
            instruccion=(
                f"Reporta telemetría de {bus_id} en ruta {ruta}: "
                f"posicion={telemetria['posicion_gps']}, velocidad={telemetria['velocidad_kmh']} km/h."
            ),
        )

    def solicitar_retencion_conductor(
        self,
        bus_id: str,
        estacion: str,
        tiempo_retencion: int,
        velocidad_objetivo: int,
    ) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteConductor",
            performative=Performativa.REQUEST,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Solicita ejecutar retención de {tiempo_retencion}s en {estacion} "
                f"y bajar velocidad a {velocidad_objetivo} km/h en {bus_id}."
            ),
        )

    def confirmar_regulacion_aceptada(self, bus_id: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteReguladorRutaFrecuencias",
            performative=Performativa.AGREE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Confirma instrucción de regulación aceptada para {bus_id}.",
        )

    def informar_intervalo_restablecido(self, bus_id: str, ruta: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteReguladorRutaFrecuencias",
            performative=Performativa.INFORM_DONE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Informa intervalo restablecido para {bus_id} en ruta {ruta}.",
        )
