"""Agente Coordinador Operativo de Movilidad."""

from typing import Any

from agents.base_agent import AgenteBase
from communication.fipa_acl import Performativa, ProtocoloFIPA


class AgenteCoordinadorOperativoMovilidad(AgenteBase):
    nombre = "AgenteCoordinadorOperativoMovilidad"

    def reservar_y_despachar_unidad(self, bus_id: str, ruta: str) -> bool:
        estado_res = self.entorno.reservar_unidad_patio(bus_id)
        if estado_res == "reservada":
            self.entorno.despachar_unidad_reservada(bus_id, ruta)
            return True
        return False

    def confirmar_reserva_y_despacho(self, bus_id: str, estacion: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteMonitorDemandaEstaciones",
            performative=Performativa.AGREE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Confirma que {bus_id} fue reservada y despachada para atender {estacion}."
            ),
        )

    def solicitar_integracion_ruta(
        self, bus_id: str, ruta: str, estacion: str
    ) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteReguladorRutaFrecuencias",
            performative=Performativa.REQUEST,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Solicita integrar {bus_id} a la ruta {ruta} con destino prioritario {estacion}."
            ),
        )

    def confirmar_despacho_completado(self, bus_id: str, estacion: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteMonitorDemandaEstaciones",
            performative=Performativa.INFORM_DONE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Confirma despacho completado de {bus_id} para {estacion}.",
        )

    def solicitar_coordinacion_apoyo(
        self, bus_apoyo: str, ruta: str, estacion: str
    ) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteReguladorRutaFrecuencias",
            performative=Performativa.REQUEST,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Solicita coordinar el ingreso de {bus_apoyo} a la ruta {ruta} "
                f"para cubrir {estacion}."
            ),
        )
