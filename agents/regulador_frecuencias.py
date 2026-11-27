"""Agente Regulador de Ruta y Frecuencias."""

from typing import Any

from agents.base_agent import AgenteBase
from communication.fipa_acl import Performativa, ProtocoloFIPA
from config.settings import (
    INTERVALO_MAX_KM,
    INTERVALO_MIN_KM,
    TIEMPO_RETENCION_SEG,
    VELOCIDAD_MAXIMA_PERMITIDA_KMH,
    VELOCIDAD_REGULACION_KMH,
)


class AccionRegulacion:
    BAJAR = "bajar"        # Intervalo demasiado corto: retener y bajar velocidad
    SUBIR = "subir"        # Intervalo demasiado largo: subir a la velocidad permitida
    MANTENER = "mantener"  # Intervalo dentro de la tolerancia: no se envía instrucción


def _km(posicion_gps: str) -> float:
    # "Km 4.20" -> 4.2
    return float(posicion_gps.replace("Km", "").split()[0])


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

    def decidir_ajuste(
        self, telemetria_delantero: dict[str, Any], telemetria_trasero: dict[str, Any]
    ) -> dict[str, Any]:
        """Evalúa el intervalo de paso contra la tolerancia y decide la corrección (basado en metas)."""
        intervalo_km = round(
            _km(telemetria_delantero["posicion_gps"]) - _km(telemetria_trasero["posicion_gps"]), 2
        )
        if intervalo_km < INTERVALO_MIN_KM:
            accion = AccionRegulacion.BAJAR
            velocidad_objetivo = VELOCIDAD_REGULACION_KMH
            tiempo_retencion = TIEMPO_RETENCION_SEG
        elif intervalo_km > INTERVALO_MAX_KM:
            accion = AccionRegulacion.SUBIR
            velocidad_objetivo = VELOCIDAD_MAXIMA_PERMITIDA_KMH
            tiempo_retencion = 0
        else:
            accion = AccionRegulacion.MANTENER
            velocidad_objetivo = telemetria_trasero["velocidad_kmh"]
            tiempo_retencion = 0
        print(
            f"[REGULADOR] Intervalo={intervalo_km} km "
            f"(tolerancia {INTERVALO_MIN_KM}-{INTERVALO_MAX_KM} km) -> decisión: {accion.upper()}"
        )
        return {
            "accion": accion,
            "intervalo_km": intervalo_km,
            "velocidad_objetivo": velocidad_objetivo,
            "tiempo_retencion": tiempo_retencion,
        }

    def ordenar_ajuste_marcha(
        self, bus_id: str, estacion: str, decision: dict[str, Any]
    ) -> dict[str, Any]:
        # Pide a la Unidad Vehicular configurar los parámetros de marcha que verá el conductor
        if decision["accion"] == AccionRegulacion.BAJAR:
            detalle = (
                f"intervalo de {decision['intervalo_km']} km, riesgo de agrupamiento. "
                f"Configura retención de {decision['tiempo_retencion']}s en {estacion} "
                f"y velocidad objetivo {decision['velocidad_objetivo']} km/h"
            )
        else:
            detalle = (
                f"intervalo de {decision['intervalo_km']} km, hueco largo en la ruta. "
                f"Configura velocidad objetivo {decision['velocidad_objetivo']} km/h"
            )
        return self.enviar_mensaje(
            receiver="AgenteUnidadVehicular",
            performative=Performativa.REQUEST,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Solicita ajustar la marcha de {bus_id}: {detalle}.",
        )

    def confirmar_frecuencia_cubierta(self, ruta: str, bus_apoyo: str) -> dict[str, Any]:
        return self.enviar_mensaje(
            receiver="AgenteCoordinadorOperativoMovilidad",
            performative=Performativa.INFORM_DONE,
            protocol=ProtocoloFIPA.REQUEST,
            instruccion=f"Confirma frecuencia cubierta en ruta {ruta} con {bus_apoyo}.",
        )
