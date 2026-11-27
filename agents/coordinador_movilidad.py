"""Agente Coordinador Operativo de Movilidad."""

from typing import Any

from agents.base_agent import AgenteBase
from communication.fipa_acl import Performativa, ProtocoloFIPA


class AgenteCoordinadorOperativoMovilidad(AgenteBase):
    nombre = "AgenteCoordinadorOperativoMovilidad"

    def evaluar_reserva(self) -> tuple[str, str] | None:
        # Busca una unidad libre en patio y la reserva. Devuelve (bus, código) o None si no hay.
        bus_id = self.entorno.buscar_unidad_disponible()
        if bus_id is None:
            return None
        codigo = self.entorno.reservar_unidad_patio(bus_id)
        return (bus_id, codigo) if codigo else None

    def aceptar_reserva(self, bus_id: str, codigo_reserva: str, estacion: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteMonitorDemandaEstaciones",
            performative=Performativa.AGREE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Acepta la solicitud: {bus_id} quedó reservada con el código {codigo_reserva} "
                f"para atender {estacion}."
            ),
        )

    def rechazar_reserva(self, estacion: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteMonitorDemandaEstaciones",
            performative=Performativa.REFUSE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Rechaza la reserva para {estacion}: no hay unidades disponibles en patio."
            ),
        )

    def despachar_unidad(self, bus_id: str, ruta: str, codigo_reserva: str) -> None:
        self.entorno.despachar_unidad_reservada(bus_id, ruta, codigo_reserva)

    def aceptar_despacho(self, bus_id: str, codigo_reserva: str, ruta: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteMonitorDemandaEstaciones",
            performative=Performativa.AGREE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Acepta despachar {bus_id} (reserva {codigo_reserva}) hacia la ruta {ruta}."
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
