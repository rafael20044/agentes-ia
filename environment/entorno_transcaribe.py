"""Entorno compartido (<<environment>> EntornoUrbanoTranscaribe)."""

from typing import Any


class EntornoUrbanoTranscaribe:
    """Modela el estado físico compartido de estaciones y flota de Transcaribe."""

    def __init__(self):
        self.estaciones: dict[str, dict[str, Any]] = {
            "Estacion_Bazurto": {"aforo": 140, "tiempo_espera_min": 21.0, "umbral": 100},
            "Estacion_Delicias": {"aforo": 115, "tiempo_espera_min": 16.5, "umbral": 100},
        }
        self.buses: dict[str, dict[str, Any]] = {
            "Bus_T101": {"ruta": "T101", "posicion_gps": "Km 4.20", "velocidad_kmh": 42, "estado": "en_ruta"},
            "Bus_T104": {"ruta": "T101", "posicion_gps": "Km 4.08", "velocidad_kmh": 48, "estado": "en_ruta"},
            "Bus_Reserva_01": {"ruta": "Patio", "posicion_gps": "Patio_Portal", "velocidad_kmh": 0, "estado": "disponible"},
            "Bus_Apoyo_02": {"ruta": "Patio", "posicion_gps": "Patio_Portal", "velocidad_kmh": 0, "estado": "disponible"},
        }

    # --- Percepciones ---

    def consultar_estado_estacion(self, estacion_x: str) -> dict[str, Any]:
        datos = self.estaciones[estacion_x]
        print(
            f"[ENTORNO] Consulta {estacion_x} -> "
            f"aforo={datos['aforo']}, espera={datos['tiempo_espera_min']} min"
        )
        return {"estacion": estacion_x, **datos}

    def consultar_telemetria_bus(self, bus_id: str) -> dict[str, Any]:
        return dict(self.buses[bus_id])

    # --- Actuadores sobre el entorno ---

    def reservar_unidad_patio(self, bus_id: str) -> str:
        if self.buses[bus_id]["estado"] == "disponible":
            self.buses[bus_id]["estado"] = "reservada"
            print(f"[ENTORNO] {bus_id} marcada como RESERVADA en patio.")
            return "reservada"
        return "no_disponible"

    def despachar_unidad_reservada(self, bus_id: str, ruta_x: str) -> str:
        if self.buses[bus_id]["estado"] == "reservada":
            self.buses[bus_id]["estado"] = "despachada"
            self.buses[bus_id]["ruta"] = ruta_x
            print(f"[ENTORNO] {bus_id} DESPACHADA hacia ruta {ruta_x}.")
            return "despachada"
        raise ValueError(f"No se puede despachar {bus_id} sin reservarla primero.")

    def desplazamiento_hacia_estacion(self, bus_id: str, estacion_x: str) -> None:
        self.buses[bus_id]["estado"] = "en_ruta"
        self.buses[bus_id]["velocidad_kmh"] = 40
        self.estaciones[estacion_x]["aforo"] = max(0, self.estaciones[estacion_x]["aforo"] - 65)
        self.estaciones[estacion_x]["tiempo_espera_min"] = 6.0
        print(
            f"[ENTORNO] {bus_id} en desplazamiento hacia {estacion_x}. "
            f"Nuevo aforo: {self.estaciones[estacion_x]['aforo']}."
        )

    def retener_bus_y_ajustar_velocidad(
        self, bus_id: str, tiempo_retencion_x: int, velocidad_objetivo_x: int
    ) -> None:
        self.buses[bus_id]["velocidad_kmh"] = velocidad_objetivo_x
        self.buses[bus_id]["posicion_gps"] = "Km 3.85 (intervalo restablecido)"
        print(
            f"[ENTORNO] {bus_id} retenido {tiempo_retencion_x}s "
            f"y velocidad ajustada a {velocidad_objetivo_x} km/h."
        )
