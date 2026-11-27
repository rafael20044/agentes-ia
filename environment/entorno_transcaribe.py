"""Entorno compartido (<<environment>> EntornoUrbanoTranscaribe)."""

from typing import Any


class EntornoUrbanoTranscaribe:
    """Modela el estado físico compartido de estaciones y flota de Transcaribe."""

    def __init__(self):
        # Estado inicial de estaciones troncales con saturación (aforo > umbral y espera > 15 min)
        self.estaciones: dict[str, dict[str, Any]] = {
            "Estacion_Bazurto": {"aforo": 140, "tiempo_espera_min": 21.0, "umbral": 100},
            "Estacion_Maria_Auxiliadora": {"aforo": 115, "tiempo_espera_min": 16.5, "umbral": 100},
        }
        # Flota en operación sobre la troncal expresa T100E (riesgo de agrupamiento) y buses en Patio Portal
        self.buses: dict[str, dict[str, Any]] = {
            "Bus_T100E_01": {"ruta": "T100E", "posicion_gps": "Km 4.20", "velocidad_kmh": 42, "estado": "en_ruta"},
            "Bus_T100E_02": {"ruta": "T100E", "posicion_gps": "Km 4.08", "velocidad_kmh": 48, "estado": "en_ruta"},
            "Bus_Reserva_01": {"ruta": "Patio", "posicion_gps": "Patio_Portal", "velocidad_kmh": 0, "estado": "disponible"},
            "Bus_Apoyo_02": {"ruta": "Patio", "posicion_gps": "Patio_Portal", "velocidad_kmh": 0, "estado": "disponible"},
        }
        self._consecutivo_reserva = 0

    # --- Percepciones (lectura del estado del entorno) ---

    def consultar_estado_estacion(self, estacion_x: str) -> dict[str, Any]:
        datos = self.estaciones[estacion_x]
        print(
            f"[ENTORNO] Consulta {estacion_x} -> "
            f"aforo={datos['aforo']}, espera={datos['tiempo_espera_min']} min"
        )
        return {"estacion": estacion_x, **datos}

    def consultar_telemetria_bus(self, bus_id: str) -> dict[str, Any]:
        return dict(self.buses[bus_id])

    # --- Actuadores (modifican el estado físico del entorno) ---

    def buscar_unidad_disponible(self) -> str | None:
        # Primera unidad del patio que no esté reservada ni despachada
        for bus_id, datos in self.buses.items():
            if datos["ruta"] == "Patio" and datos["estado"] == "disponible":
                return bus_id
        return None

    def reservar_unidad_patio(self, bus_id: str) -> str | None:
        # Devuelve el código de la reserva, o None si la unidad ya no está disponible
        if self.buses[bus_id]["estado"] != "disponible":
            return None
        self._consecutivo_reserva += 1
        codigo = f"RES-{self._consecutivo_reserva:03d}"
        self.buses[bus_id]["estado"] = "reservada"
        self.buses[bus_id]["reserva"] = codigo
        print(f"[ENTORNO] {bus_id} marcada como RESERVADA en patio con código {codigo}.")
        return codigo

    def despachar_unidad_reservada(self, bus_id: str, ruta_x: str, codigo_reserva: str) -> str:
        # Precondición: solo se despacha la unidad que tiene esa reserva
        bus = self.buses[bus_id]
        if bus["estado"] == "reservada" and bus.get("reserva") == codigo_reserva:
            self.buses[bus_id]["estado"] = "despachada"
            self.buses[bus_id]["ruta"] = ruta_x
            print(f"[ENTORNO] {bus_id} DESPACHADA hacia ruta {ruta_x}.")
            return "despachada"
        raise ValueError(f"No se puede despachar {bus_id} sin la reserva {codigo_reserva}.")

    def desplazamiento_hacia_estacion(self, bus_id: str, estacion_x: str) -> None:
        # El bus entra en circulación y evacúa pasajeros en la estación saturada
        self.buses[bus_id]["estado"] = "en_ruta"
        self.buses[bus_id]["posicion_gps"] = f"En ruta hacia {estacion_x}"
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
        # Mientras se retiene el bus de atrás, el bus delantero avanza y se recupera el intervalo
        if "Bus_T100E_01" in self.buses:
            self.buses["Bus_T100E_01"]["posicion_gps"] = "Km 4.85"
        self.buses[bus_id]["velocidad_kmh"] = velocidad_objetivo_x
        self.buses[bus_id]["posicion_gps"] = "Km 4.15 (intervalo restablecido)"
        print(
            f"[ENTORNO] {bus_id} retenido {tiempo_retencion_x}s "
            f"y velocidad ajustada a {velocidad_objetivo_x} km/h."
        )

    def ajustar_velocidad(self, bus_id: str, velocidad_objetivo_x: int) -> None:
        # El bus de atrás acelera hasta la velocidad permitida para cerrar el hueco
        self.buses[bus_id]["velocidad_kmh"] = velocidad_objetivo_x
        print(f"[ENTORNO] {bus_id} velocidad ajustada a {velocidad_objetivo_x} km/h.")
