"""Agente Monitor de Demanda en Estaciones."""

from typing import Any

from agents.base_agent import AgenteBase
from communication.fipa_acl import Performativa, ProtocoloFIPA


class AgenteMonitorDemandaEstaciones(AgenteBase):
    nombre = "AgenteMonitorDemandaEstaciones"

    def percibir_estacion(self, estacion: str) -> dict[str, Any]:
        return self.entorno.consultar_estado_estacion(estacion)

    def detectar_saturacion(self, datos_estacion: dict[str, Any]) -> bool:
        # Regla de decisión: hay saturación si supera el umbral de aforo o los 15 min de espera
        return (
            datos_estacion["aforo"] > datos_estacion["umbral"]
            or datos_estacion.get("tiempo_espera_min", 0.0) > 15.0
        )

    def notificar_alerta_congestion(
        self, estacion: str, aforo: int, tiempo_espera: float
    ) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteReguladorRutaFrecuencias",
            performative=Performativa.INFORM,
            protocol=ProtocoloFIPA.INFORM,
            instruccion=(
                f"Notifica alerta_congestion en {estacion} con aforo={aforo} "
                f"y tiempo_espera={tiempo_espera}."
            ),
        )

    def solicitar_reserva_unidad(self, estacion: str, ruta: str) -> dict[str, Any]:
        # Primer paso: pedir que se reserve una unidad. Reserva y despacho son dos solicitudes distintas.
        return self.enviar_mensaje(
            receiver="AgenteCoordinadorOperativoMovilidad",
            performative=Performativa.REQUEST,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Solicita reservar una unidad de patio para reforzar {estacion} en la ruta {ruta} "
                "por saturación crítica."
            ),
        )

    def solicitar_despacho(
        self, bus_id: str, codigo_reserva: str, ruta: str, estacion: str
    ) -> dict[str, Any]:
        # Segundo paso: pedir el despacho de la unidad que quedó reservada, citando su código
        return self.enviar_mensaje(
            receiver="AgenteCoordinadorOperativoMovilidad",
            performative=Performativa.REQUEST,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Solicita despachar {bus_id} con la reserva {codigo_reserva} "
                f"hacia {estacion} en la ruta {ruta}."
            ),
        )

    def informar_aumento_aforo_post_retencion(
        self, estacion: str, aforo: int
    ) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteReguladorRutaFrecuencias",
            performative=Performativa.INFORM,
            protocol=ProtocoloFIPA.INFORM,
            instruccion=f"Informa aumento de aforo en {estacion}: aforo={aforo} tras la retención.",
        )

    def enviar_alerta_demanda_acumulada(
        self, estacion: str, aforo: int, tiempo_espera: float
    ) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteCoordinadorOperativoMovilidad",
            performative=Performativa.INFORM,
            protocol=ProtocoloFIPA.INFORM,
            instruccion=(
                f"Envía alerta de demanda acumulada en {estacion}: "
                f"aforo={aforo}, espera={tiempo_espera} min."
            ),
        )
