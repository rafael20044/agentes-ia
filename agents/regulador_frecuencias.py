"""Agente Regulador de Ruta y Frecuencias."""

from typing import Any

from agents.base_agent import AgenteBase
from communication.fipa_acl import Performativa, ProtocoloFIPA


class AgenteReguladorRutaFrecuencias(AgenteBase):
    nombre = "AgenteReguladorRutaFrecuencias"

    def predecir_eta(self, bus_id: str, estacion: str) -> str:
        """Simulación de predicción de ETA hacia la estación objetivo."""
        return "7 min"

    def asignar_recorrido_refuerzo(
        self, bus_id: str, ruta: str, estacion: str, eta: str
    ) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteUnidadVehicular",
            performative=Performativa.REQUEST,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Asigna recorrido de refuerzo a {bus_id} en ruta {ruta} "
                f"hacia {estacion} con eta={eta}."
            ),
        )

    def confirmar_unidad_integrada(self, bus_id: str, ruta: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteCoordinadorOperativoMovilidad",
            performative=Performativa.AGREE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Confirma unidad {bus_id} integrada al corredor {ruta}.",
        )

    def informar_refuerzo_activo(self, bus_id: str, ruta: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteCoordinadorOperativoMovilidad",
            performative=Performativa.INFORM_DONE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Informa refuerzo operativo activo con {bus_id} en {ruta}.",
        )

    def ordenar_regulacion_bunching(
        self,
        bus_id: str,
        estacion: str,
        tiempo_retencion: int,
        velocidad_objetivo: int,
    ) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteUnidadVehicular",
            performative=Performativa.REQUEST,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=(
                f"Riesgo de bunching detectado. Ordena regular marcha de {bus_id} en {estacion}: "
                f"retención de {tiempo_retencion}s y velocidad objetivo {velocidad_objetivo} km/h."
            ),
        )

    def confirmar_frecuencia_cubierta(self, ruta: str, bus_apoyo: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteCoordinadorOperativoMovilidad",
            performative=Performativa.INFORM_DONE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Confirma frecuencia cubierta en ruta {ruta} con {bus_apoyo}.",
        )
