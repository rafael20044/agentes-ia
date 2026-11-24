import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

load_dotenv()

# Inicializar cliente (requiere variable de entorno GEMINI_API_KEY en .env)
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
# 1. ENTORNO COMPARTIDO (<<environment>> EntornoUrbanoTranscaribe)
# ==============================================================================
class EntornoUrbanoTranscaribe:
    def __init__(self):
        self.estaciones = {
            "Estacion_Bazurto": {"aforo": 140, "tiempo_espera_min": 21.0, "umbral": 100},
            "Estacion_Delicias": {"aforo": 115, "tiempo_espera_min": 16.5, "umbral": 100},
        }
        self.buses = {
            "Bus_T101": {"ruta": "T101", "posicion_gps": "Km 4.20", "velocidad_kmh": 42, "estado": "en_ruta"},
            "Bus_T104": {"ruta": "T101", "posicion_gps": "Km 4.08", "velocidad_kmh": 48, "estado": "en_ruta"},
            "Bus_Reserva_01": {"ruta": "Patio", "posicion_gps": "Patio_Portal", "velocidad_kmh": 0, "estado": "disponible"},
            "Bus_Apoyo_02": {"ruta": "Patio", "posicion_gps": "Patio_Portal", "velocidad_kmh": 0, "estado": "disponible"},
        }
        self.bd_trazabilidad = []

    def registrar_mensaje_fipa(self, msg: dict):
        self.bd_trazabilidad.append(msg)
        print(f"[FIPA-ACL] {msg['sender']} -> {msg['receiver']} | <<ACL:{msg['performative'].upper()}>>")
        print(f"           Contenido: {json.dumps(msg['content'], ensure_ascii=False)}")

    def consultar_estado_estacion(self, estacion_x: str) -> dict:
        datos = self.estaciones[estacion_x]
        print(f"[ENTORNO] Consulta {estacion_x} -> aforo={datos['aforo']}, espera={datos['tiempo_espera_min']} min")
        return {"estacion": estacion_x, **datos}

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

    def desplazamiento_hacia_estacion(self, bus_id: str, estacion_x: str):
        self.buses[bus_id]["estado"] = "en_ruta"
        self.buses[bus_id]["velocidad_kmh"] = 40
        self.estaciones[estacion_x]["aforo"] = max(0, self.estaciones[estacion_x]["aforo"] - 65)
        self.estaciones[estacion_x]["tiempo_espera_min"] = 6.0
        print(f"[ENTORNO] {bus_id} en desplazamiento hacia {estacion_x}. Nuevo aforo: {self.estaciones[estacion_x]['aforo']}.")

    def retener_bus_y_ajustar_velocidad(self, bus_id: str, tiempo_retencion_x: int, velocidad_objetivo_x: int):
        self.buses[bus_id]["velocidad_kmh"] = velocidad_objetivo_x
        self.buses[bus_id]["posicion_gps"] = "Km 3.85 (intervalo restablecido)"
        print(f"[ENTORNO] {bus_id} retenido {tiempo_retencion_x}s y velocidad ajustada a {velocidad_objetivo_x} km/h.")


# ==============================================================================
# 2. MOTOR DE COMUNICACIÓN FIPA ACL CON GOOGLE GENAI SDK
# ==============================================================================
def emitir_fipa_acl(
    entorno: EntornoUrbanoTranscaribe,
    sender: str,
    receiver: str,
    performative: str,
    protocol: str,
    instruccion: str,
    max_reintentos: int = 3,
    espera_base: float = 2.0,
) -> dict:
    global modelo_actual_idx
    system_prompt = (
        f"Eres el agente '{sender}' del Sistema Multiagente de Transcaribe. "
        "Responde UNICAMENTE con un objeto JSON válido que siga el estándar FIPA ACL con exactamente estas llaves: "
        "performative, sender, receiver, content, ontology, protocol. "
        f"Usa performative='{performative}', sender='{sender}', receiver='{receiver}', "
        f"ontology='Transcaribe', protocol='{protocol}'."
    )

    ultimo_error = None
    while modelo_actual_idx < len(MODELOS):
        modelo = MODELOS[modelo_actual_idx]
        for intento in range(1, max_reintentos + 1):
            try:
                response = client.models.generate_content(
                    model=modelo,
                    contents=instruccion,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                msg = json.loads(response.text)
                entorno.registrar_mensaje_fipa(msg)
                return msg
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
# 3. DIAGRAMA DE SECUENCIA 1 (CU-01): CONGESTIÓN, RESERVA Y DESPACHO
# ==============================================================================
def ejecutar_cu01(entorno: EntornoUrbanoTranscaribe):
    print("\n" + "=" * 75)
    print("CU-01: GESTIÓN DE CONGESTIÓN, RESERVA DE FLOTA Y DESPACHO A ESTACIÓN")
    print("=" * 75)

    estacion_x = "Estacion_Bazurto"
    ruta_x = "T101"
    bus_reserva_x = "Bus_Reserva_01"

    # 1. Consulta al entorno y detección de saturación
    datos = entorno.consultar_estado_estacion(estacion_x)
    if datos["aforo"] <= datos["umbral"]:
        print("Aforo dentro de parámetros normales.")
        return

    emitir_fipa_acl(
        entorno, "AgenteMonitorDemandaEstaciones", "AgenteReguladorRutaFrecuencias",
        "inform", "FIPA-Inform",
        f"Notifica alerta_congestion en {estacion_x} con aforo={datos['aforo']} y tiempo_espera={datos['tiempo_espera_min']}."
    )
    req_refuerzo = emitir_fipa_acl(
        entorno, "AgenteMonitorDemandaEstaciones", "AgenteCoordinadorOperativoMovilidad",
        "request", "FIPA-Request",
        f"Solicita refuerzo para {estacion_x} en la ruta {ruta_x} por saturación crítica."
    )

    # 2. Reserva y posterior despacho desde patio
    estado_res = entorno.reservar_unidad_patio(bus_reserva_x)
    if estado_res == "reservada":
        entorno.despachar_unidad_reservada(bus_reserva_x, ruta_x)

    emitir_fipa_acl(
        entorno, "AgenteCoordinadorOperativoMovilidad", "AgenteMonitorDemandaEstaciones",
        "agree", "FIPA-Request",
        f"Confirma que {bus_reserva_x} fue reservada y despachada para atender {estacion_x}."
    )

    # 3. Integración a ruta y ejecución a bordo
    emitir_fipa_acl(
        entorno, "AgenteCoordinadorOperativoMovilidad", "AgenteReguladorRutaFrecuencias",
        "request", "FIPA-Request",
        f"Solicita integrar {bus_reserva_x} a la ruta {ruta_x} con destino prioritario {estacion_x}."
    )
    eta_x = "7 min"  # Resultado simulado de predecirETA()
    emitir_fipa_acl(
        entorno, "AgenteReguladorRutaFrecuencias", "AgenteUnidadVehicular",
        "request", "FIPA-Request",
        f"Asigna recorrido de refuerzo a {bus_reserva_x} en ruta {ruta_x} hacia {estacion_x} con eta={eta_x}."
    )
    emitir_fipa_acl(
        entorno, "AgenteUnidadVehicular", "AgenteConductor",
        "request", "FIPA-Request",
        f"Solicita iniciar recorrido de refuerzo en {bus_reserva_x} hacia {estacion_x} (ruta {ruta_x})."
    )

    # Cadena de aceptación (AGREE)
    emitir_fipa_acl(
        entorno, "AgenteConductor", "AgenteUnidadVehicular",
        "agree", "FIPA-Request", f"Acepta iniciar el recorrido en {bus_reserva_x}."
    )
    emitir_fipa_acl(
        entorno, "AgenteUnidadVehicular", "AgenteReguladorRutaFrecuencias",
        "agree", "FIPA-Request", f"Confirma recorrido aceptado por el conductor de {bus_reserva_x}."
    )
    emitir_fipa_acl(
        entorno, "AgenteReguladorRutaFrecuencias", "AgenteCoordinadorOperativoMovilidad",
        "agree", "FIPA-Request", f"Confirma unidad {bus_reserva_x} integrada al corredor {ruta_x}."
    )

    # 4. Ejecución física en entorno y cierre en cadena (INFORM-DONE)
    entorno.desplazamiento_hacia_estacion(bus_reserva_x, estacion_x)

    emitir_fipa_acl(
        entorno, "AgenteConductor", "AgenteUnidadVehicular",
        "inform-done", "FIPA-Request", f"Informa desplazamiento iniciado de {bus_reserva_x} hacia {estacion_x}."
    )
    emitir_fipa_acl(
        entorno, "AgenteUnidadVehicular", "AgenteReguladorRutaFrecuencias",
        "inform-done", "FIPA-Request", f"Informa {bus_reserva_x} en ruta hacia {estacion_x}."
    )
    emitir_fipa_acl(
        entorno, "AgenteReguladorRutaFrecuencias", "AgenteCoordinadorOperativoMovilidad",
        "inform-done", "FIPA-Request", f"Informa refuerzo operativo activo con {bus_reserva_x} en {ruta_x}."
    )
    emitir_fipa_acl(
        entorno, "AgenteCoordinadorOperativoMovilidad", "AgenteMonitorDemandaEstaciones",
        "inform-done", "FIPA-Request", f"Confirma despacho completado de {bus_reserva_x} para {estacion_x}."
    )


# ==============================================================================
# 4. DIAGRAMA DE SECUENCIA 2 (CU-02): REGULACIÓN DE FRECUENCIAS Y BUNCHING
# ==============================================================================
def ejecutar_cu02(entorno: EntornoUrbanoTranscaribe):
    print("\n" + "=" * 75)
    print("CU-02: REGULACIÓN DE FRECUENCIAS, PREVENCIÓN DE BUNCHING Y RESPALDO")
    print("=" * 75)

    bus_x = "Bus_T104"
    ruta_x = "T101"
    estacion_x = "Estacion_Bazurto"
    estacion_y = "Estacion_Delicias"
    bus_apoyo_x = "Bus_Apoyo_02"
    tiempo_retencion_x = 45
    velocidad_objetivo_x = 30

    telemetria = entorno.buses[bus_x]

    # 1. Telemetría y regulación táctica en vía
    emitir_fipa_acl(
        entorno, "AgenteUnidadVehicular", "AgenteReguladorRutaFrecuencias",
        "inform", "FIPA-Inform",
        f"Reporta telemetría de {bus_x} en ruta {ruta_x}: posicion={telemetria['posicion_gps']}, velocidad={telemetria['velocidad_kmh']} km/h."
    )
    emitir_fipa_acl(
        entorno, "AgenteReguladorRutaFrecuencias", "AgenteUnidadVehicular",
        "request", "FIPA-Request",
        f"Riesgo de bunching detectado. Ordena regular marcha de {bus_x} en {estacion_x}: retención de {tiempo_retencion_x}s y velocidad objetivo {velocidad_objetivo_x} km/h."
    )
    emitir_fipa_acl(
        entorno, "AgenteUnidadVehicular", "AgenteConductor",
        "request", "FIPA-Request",
        f"Solicita ejecutar retención de {tiempo_retencion_x}s en {estacion_x} y bajar velocidad a {velocidad_objetivo_x} km/h en {bus_x}."
    )
    emitir_fipa_acl(
        entorno, "AgenteConductor", "AgenteUnidadVehicular",
        "agree", "FIPA-Request", f"Confirma que la maniobra es segura y la acepta para {bus_x}."
    )
    emitir_fipa_acl(
        entorno, "AgenteUnidadVehicular", "AgenteReguladorRutaFrecuencias",
        "agree", "FIPA-Request", f"Confirma instrucción de regulación aceptada para {bus_x}."
    )

    entorno.retener_bus_y_ajustar_velocidad(bus_x, tiempo_retencion_x, velocidad_objetivo_x)

    emitir_fipa_acl(
        entorno, "AgenteConductor", "AgenteUnidadVehicular",
        "inform-done", "FIPA-Request", f"Informa retención y ajuste de velocidad completados en {bus_x}."
    )
    emitir_fipa_acl(
        entorno, "AgenteUnidadVehicular", "AgenteReguladorRutaFrecuencias",
        "inform-done", "FIPA-Request", f"Informa intervalo restablecido para {bus_x} en ruta {ruta_x}."
    )

    # 2. Impacto en demanda y respaldo con reserva
    datos_y = entorno.consultar_estado_estacion(estacion_y)

    emitir_fipa_acl(
        entorno, "AgenteMonitorDemandaEstaciones", "AgenteReguladorRutaFrecuencias",
        "inform", "FIPA-Inform",
        f"Informa aumento de aforo en {estacion_y}: aforo={datos_y['aforo']} tras la retención."
    )
    emitir_fipa_acl(
        entorno, "AgenteMonitorDemandaEstaciones", "AgenteCoordinadorOperativoMovilidad",
        "inform", "FIPA-Inform",
        f"Envía alerta de demanda acumulada en {estacion_y}: aforo={datos_y['aforo']}, espera={datos_y['tiempo_espera_min']} min."
    )

    if entorno.reservar_unidad_patio(bus_apoyo_x) == "reservada":
        entorno.despachar_unidad_reservada(bus_apoyo_x, ruta_x)

    emitir_fipa_acl(
        entorno, "AgenteCoordinadorOperativoMovilidad", "AgenteReguladorRutaFrecuencias",
        "request", "FIPA-Request",
        f"Solicita coordinar el ingreso de {bus_apoyo_x} a la ruta {ruta_x} para cubrir {estacion_y}."
    )
    emitir_fipa_acl(
        entorno, "AgenteReguladorRutaFrecuencias", "AgenteCoordinadorOperativoMovilidad",
        "inform-done", "FIPA-Request",
        f"Confirma frecuencia cubierta en ruta {ruta_x} con {bus_apoyo_x}."
    )


# ==============================================================================
# 5. EJECUCIÓN PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    entorno = EntornoUrbanoTranscaribe()
    ejecutar_cu01(entorno)
    ejecutar_cu02(entorno)

    print("\n" + "=" * 75)
    print(f"SIMULACIÓN COMPLETA | Total mensajes FIPA ACL registrados en BD: {len(entorno.bd_trazabilidad)}")
    print("Estado final de estaciones:", json.dumps(entorno.estaciones, ensure_ascii=False))
    print("Estado final de flota:", json.dumps(entorno.buses, ensure_ascii=False))
