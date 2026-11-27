"""Caso de Uso 2 (CU-02): Regulación de frecuencias, prevención de agrupamiento y respaldo."""

from agents import (
    AgenteConductor,
    AgenteCoordinadorOperativoMovilidad,
    AgenteMonitorDemandaEstaciones,
    AgenteReguladorRutaFrecuencias,
    AgenteUnidadVehicular,
)
from agents.regulador_frecuencias import AccionRegulacion
from use_cases.protocolo_reserva import reservar_y_despachar


def ejecutar_cu02(
    monitor: AgenteMonitorDemandaEstaciones,
    coordinador: AgenteCoordinadorOperativoMovilidad,
    regulador: AgenteReguladorRutaFrecuencias,
    unidad: AgenteUnidadVehicular,
    conductor: AgenteConductor,
) -> None:
    print("\n" + "=" * 75)
    print("CU-02: REGULACIÓN DE FRECUENCIAS, PREVENCIÓN DE AGRUPAMIENTO Y RESPALDO")
    print("=" * 75)

    # Escenario sobre la troncal expresa T100E (Bus_T100E_02 alcanzando a Bus_T100E_01)
    bus_delantero = "Bus_T100E_01"
    bus_x = "Bus_T100E_02"
    ruta_x = "T100E"
    estacion_x = "Estacion_Cuatro_Vientos"
    estacion_y = "Estacion_Maria_Auxiliadora"
    monitor.bus.iniciar_conversacion("cu02-t100e")

    # 1. Telemetría de los dos buses y evaluación del intervalo por el Regulador
    telemetria_delantero = unidad.reportar_telemetria(bus_delantero, ruta_x)
    telemetria_x = unidad.reportar_telemetria(bus_x, ruta_x)
    decision = regulador.decidir_ajuste(telemetria_delantero, telemetria_x)

    # 2. alt: bajar / subir / mantener
    if decision["accion"] == AccionRegulacion.MANTENER:
        print("[CU-02] Intervalo dentro de la tolerancia: no se envía ninguna instrucción.")
    else:
        regulador.ordenar_ajuste_marcha(bus_x, estacion_x, decision)
        unidad.solicitar_ajuste_conductor(bus_x, estacion_x, decision)
        conductor.aceptar_maniobra_regulacion(bus_x)
        unidad.confirmar_regulacion_aceptada(bus_x)
        conductor.ejecutar_ajuste(bus_x, decision)
        unidad.informar_intervalo_restablecido(bus_x, ruta_x)

    # 3. Evaluación de saturación en la siguiente parada (María Auxiliadora) y despacho de apoyo
    datos_y = monitor.percibir_estacion(estacion_y)
    if not monitor.detectar_saturacion(datos_y):
        return
    monitor.bus.iniciar_conversacion("cu02-maria-auxiliadora")
    monitor.informar_aumento_aforo_post_retencion(estacion_y, datos_y["aforo"])
    monitor.enviar_alerta_demanda_acumulada(
        estacion_y, datos_y["aforo"], datos_y["tiempo_espera_min"]
    )
    resultado = reservar_y_despachar(monitor, coordinador, estacion_y, ruta_x)
    if resultado is None:
        return
    bus_apoyo_x, _ = resultado
    coordinador.solicitar_coordinacion_apoyo(bus_apoyo_x, ruta_x, estacion_y)
    regulador.confirmar_frecuencia_cubierta(ruta_x, bus_apoyo_x)
