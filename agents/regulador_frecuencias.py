"""Agente Regulador de Ruta y Frecuencias."""

from typing import Any

from agents.base_agent import AgenteBase
from communication.fipa_acl import Performativa, ProtocoloFIPA


class AgenteReguladorRutaFrecuencias(AgenteBase):
    nombre = "AgenteReguladorRutaFrecuencias"

    def predecir_eta(self, bus_id: str, estacion: str) -> str:
        """Cálculo lineal de ETA en función de distancia, velocidad promedio y congestión."""
        datos_estacion = self.entorno.estaciones.get(estacion, {"aforo": 100, "umbral": 100})
        distancia_estimada_km = 4.2
        velocidad_promedio_kmh = 38.0
        # Tiempo base en minutos más penalización proporcional al nivel de saturación
        tiempo_base_min = (distancia_estimada_km / velocidad_promedio_kmh) * 60.0
        factor_congestion = (datos_estacion["aforo"] / max(1, datos_estacion["umbral"])) * 0.55
        eta_min = round(tiempo_base_min + factor_congestion, 1)
        return f"{eta_min} min"

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
