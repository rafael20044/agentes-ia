import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

client = genai.Client(
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=1)
    )
)
MODELOS = [
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
]
modelo_actual_idx = 0

# ==============================================================================
# 1. DEFINICIÓN DEL ENTORNO (<<environment>> EntornoUrbanoTranscaribe)
# ==============================================================================
class EntornoUrbanoTranscaribe:
    def __init__(self):
        # Estado inicial del entorno
        self.estaciones = {
            "Estacion_Bazurto": {"aforo": 135, "tiempo_espera_min": 19, "umbral": 100}
        }
        self.buses = {
            "Bus_T101": {"ruta": "T101", "posicion_km": 4.2, "velocidad_kmh": 45, "ocupacion": 90},
            "Bus_T104": {"ruta": "T101", "posicion_km": 4.05, "velocidad_kmh": 50, "ocupacion": 30}, # A 150m del T101 (Bunching)
            "Bus_Reserva_01": {"ruta": "Patio", "posicion_km": 0.0, "velocidad_kmh": 0, "ocupacion": 0}
        }
        self.bd_trazabilidad = []

    def registrar_mensaje_fipa(self, mensaje_acl: dict):
        """Guarda cada intercambio FIPA ACL en la Base de Datos de Trazabilidad."""
        self.bd_trazabilidad.append(mensaje_acl)
        print(f"\n[BUS FIPA-ACL] {mensaje_acl['sender']} -> {mensaje_acl['receiver']} | Performativa: {mensaje_acl['performative'].upper()}")
        print(f"   Contenido: {json.dumps(mensaje_acl['content'], ensure_ascii=False)}")

    def despachar_bus_reserva(self, bus_id: str, estacion_destino: str):
        """Efecto físico en el entorno al despachar flota."""
        if bus_id in self.buses and estacion_destino in self.estaciones:
            self.buses[bus_id]["ruta"] = "Expreso_Refuerzo"
            self.buses[bus_id]["velocidad_kmh"] = 40
            # Al llegar el refuerzo, baja la congestión en el andén
            self.estaciones[estacion_destino]["aforo"] -= 60
            self.estaciones[estacion_destino]["tiempo_espera_min"] = 5
            print(f"   >>> [ENTORNO ACTUALIZADO] {bus_id} despachado a {estacion_destino}. Nuevo aforo: {self.estaciones[estacion_destino]['aforo']} usuarios.")

    def regular_bus(self, bus_id: str, nueva_velocidad: int, retencion_seg: int):
        """Efecto físico en el entorno al regular la marcha de un bus."""
        if bus_id in self.buses:
            self.buses[bus_id]["velocidad_kmh"] = nueva_velocidad
            self.buses[bus_id]["posicion_km"] -= 0.25 # Se distancia del bus de adelante
            print(f"   >>> [ENTORNO ACTUALIZADO] {bus_id} retenido {retencion_seg}s y velocidad ajustada a {nueva_velocidad} km/h.")

    def mostrar_estado(self, titulo: str):
        print(f"\n--- {titulo} ---")
        print("Estaciones:", json.dumps(self.estaciones, ensure_ascii=False))
        print("Flota:", json.dumps(self.buses, ensure_ascii=False))


# ==============================================================================
# 2. FUNCIÓN AUXILIAR PARA INVOCAR AGENTES CON GOOGLE GENAI SDK
# ==============================================================================
def ejecutar_agente(rol_sistema: str, percepcion: str, max_reintentos: int = 3, espera_base: float = 2.0) -> dict:
    global modelo_actual_idx
    ultimo_error = None

    while modelo_actual_idx < len(MODELOS):
        modelo = MODELOS[modelo_actual_idx]
        for intento in range(1, max_reintentos + 1):
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=percepcion,
                    config=types.GenerateContentConfig(
                        system_instruction=rol_sistema,
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                return json.loads(response.text)
            except errors.APIError as e:
                ultimo_error = e
                es_cuota_diaria = e.code == 429 and (
                    "PerDay" in str(e) or "per day" in str(e).lower()
                )
                if e.code == 404 or es_cuota_diaria:
                    print(f"   [API {e.code}] Modelo '{modelo}' sin cuota diaria o no disponible. Probando siguiente modelo...")
                    break
                if e.code in (429, 500, 503, 504) and intento < max_reintentos:
                    espera = espera_base * (2 ** (intento - 1))
                    print(f"   [API {e.code}] ({modelo}) Reintentando ({intento}/{max_reintentos}) en {espera:.0f}s...")
                    time.sleep(espera)
                elif e.code in (429, 500, 503, 504):
                    print(f"   [API {e.code}] Modelo '{modelo}' falló tras {intento} intentos. Probando siguiente modelo...")
                    break
                else:
                    raise
        modelo_actual_idx += 1

    raise ultimo_error


# ==============================================================================
# 3. EJECUCIÓN DE LA SIMULACIÓN EN ENTORNO COMPARTIDO
# ==============================================================================
entorno = EntornoUrbanoTranscaribe()
entorno.mostrar_estado("ESTADO INICIAL DEL ENTORNO")

# ------------------------------------------------------------------------------
# CICLO 1: Gestión de Saturación (CU-01)
# ------------------------------------------------------------------------------
print("\n[CICLO 1: MONITOREO DE ESTACIONES Y DESPACHO DE RESERVA]")

# 1. Monitor percibe el entorno
datos_estacion = entorno.estaciones["Estacion_Bazurto"]
msg_req_despacho = ejecutar_agente(
    rol_sistema="Eres AgenteMonitorDemandaEstaciones de Transcaribe. Emite mensajes FIPA ACL estrictos en JSON con llaves: performative, sender, receiver, content, ontology, protocol.",
    percepcion=f"Percibes en Estacion_Bazurto: {datos_estacion}. Como el aforo supera el umbral, envía un 'request' a 'AgenteCoordinadorOperativoMovilidad' solicitando el despacho de 'Bus_Reserva_01'."
)
entorno.registrar_mensaje_fipa(msg_req_despacho)

# 2. Coordinador evalúa y acepta (AGREE)
msg_agree_coord = ejecutar_agente(
    rol_sistema="Eres AgenteCoordinadorOperativoMovilidad de Transcaribe. Emite mensajes FIPA ACL estrictos en JSON con llaves: performative, sender, receiver, content, ontology, protocol.",
    percepcion=f"Recibiste: {msg_req_despacho}. Flota disponible en patio: {entorno.buses['Bus_Reserva_01']}. Responde con performativa 'agree' aceptando el despacho."
)
entorno.registrar_mensaje_fipa(msg_agree_coord)

# 3. Acción física sobre el entorno e INFORM-DONE
entorno.despachar_bus_reserva("Bus_Reserva_01", "Estacion_Bazurto")
msg_done_coord = ejecutar_agente(
    rol_sistema="Eres AgenteCoordinadorOperativoMovilidad. Emite mensajes FIPA ACL estrictos en JSON con llaves: performative, sender, receiver, content, ontology, protocol.",
    percepcion="Ya ejecutaste el despacho de Bus_Reserva_01 en el entorno. Envía 'inform-done' a 'AgenteMonitorDemandaEstaciones'."
)
entorno.registrar_mensaje_fipa(msg_done_coord)


# ------------------------------------------------------------------------------
# CICLO 2: Prevención de Bunching (CU-02)
# ------------------------------------------------------------------------------
print("\n[CICLO 2: REGULACIÓN DE INTERVALOS Y PREVENCIÓN DE BUNCHING]")

# 1. Unidad Vehicular reporta telemetría desde el entorno
telemetria_t104 = entorno.buses["Bus_T104"]
telemetria_t101 = entorno.buses["Bus_T101"]
msg_inf_bus = ejecutar_agente(
    rol_sistema="Eres AgenteUnidadVehicular (Bus_T104). Emite mensajes FIPA ACL estrictos en JSON con llaves: performative, sender, receiver, content, ontology, protocol.",
    percepcion=f"Tu telemetría actual es {telemetria_t104}. Envía un 'inform' a 'AgenteReguladorRutaFrecuencias' con tu posición y velocidad."
)
entorno.registrar_mensaje_fipa(msg_inf_bus)

# 2. Regulador detecta cercanía con Bus_T101 (4.2 km vs 4.05 km = 150 metros) y envía REQUEST
msg_req_reg = ejecutar_agente(
    rol_sistema="Eres AgenteReguladorRutaFrecuencias. Emite mensajes FIPA ACL estrictos en JSON con llaves: performative, sender, receiver, content, ontology, protocol.",
    percepcion=f"Recibiste {msg_inf_bus}. Sabes que Bus_T101 está en km 4.2 (a solo 150m). Envía un 'request' a 'AgenteUnidadVehicular' ordenando retención de 40 segundos y bajar velocidad a 30 km/h."
)
entorno.registrar_mensaje_fipa(msg_req_reg)

# 3. Unidad Vehicular + Conductor ejecutan en el entorno y cierran con INFORM-DONE
entorno.regular_bus("Bus_T104", nueva_velocidad=30, retencion_seg=40)
msg_done_bus = ejecutar_agente(
    rol_sistema="Eres AgenteUnidadVehicular (Bus_T104) tras confirmación del AgenteConductor. Emite mensajes FIPA ACL estrictos en JSON con llaves: performative, sender, receiver, content, ontology, protocol.",
    percepcion="El conductor ejecutó la retención y bajó la velocidad a 30 km/h. Envía 'inform-done' a 'AgenteReguladorRutaFrecuencias'."
)
entorno.registrar_mensaje_fipa(msg_done_bus)

# Mostrar el impacto real de los agentes sobre el entorno y la BD de trazabilidad
entorno.mostrar_estado("ESTADO FINAL DEL ENTORNO TRAS INTERVENCIÓN DE LOS AGENTES")
print(f"\nTotal de mensajes FIPA ACL auditados en Base de Datos de Trazabilidad: {len(entorno.bd_trazabilidad)}")