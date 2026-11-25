"""Agente Monitor de Demanda en Estaciones."""

from typing import Any

from agents.base_agent import AgenteBase
from communication.fipa_acl import Performativa, ProtocoloFIPA


class AgenteMonitorDemandaEstaciones(AgenteBase):
    nombre = "AgenteMonitorDemandaEstaciones"

    def percibir_estacion(self, estacion: str) -> dict[str, Any]:
        return self.entorno.consultar_estado_estacion(estacion)

    def detectar_saturacion(self, datos_estacion: dict[str, Any]) -> bool:
        return datos_estacion["aforo"] > datos_estacion["umbral"]

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

    def solicitar_refuerzo(self, estacion: str, ruta: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteCoordinadorOperativoMovilidad",
            performative=Performativa.REQUEST,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Solicita refuerzo para {estacion} en la ruta {ruta} por saturación crítica."
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
