"""Caso de Uso 2 (CU-02): Regulación de frecuencias, prevención de bunching y respaldo."""

from agents import (
    AgenteConductor,
    AgenteCoordinadorOperativoMovilidad,
    AgenteMonitorDemandaEstaciones,
    AgenteReguladorRutaFrecuencias,
    AgenteUnidadVehicular,
)


def ejecutar_cu02(
    monitor: AgenteMonitorDemandaEstaciones,
    coordinador: AgenteCoordinadorOperativoMovilidad,
    regulador: AgenteReguladorRutaFrecuencias,
    unidad: AgenteUnidadVehicular,
    conductor: AgenteConductor,
) -> None:
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

    # 1. Telemetría y regulación táctica en vía
    unidad.reportar_telemetria(bus_x, ruta_x)
    regulador.ordenar_regulacion_bunching(
        bus_x, estacion_x, tiempo_retencion_x, velocidad_objetivo_x
    )
    unidad.solicitar_retencion_conductor(
        bus_x, estacion_x, tiempo_retencion_x, velocidad_objetivo_x
    )
    conductor.aceptar_maniobra_regulacion(bus_x)
    unidad.confirmar_regulacion_aceptada(bus_x)

    conductor.ejecutar_retencion_y_velocidad(
        bus_x, tiempo_retencion_x, velocidad_objetivo_x
    )
    unidad.informar_intervalo_restablecido(bus_x, ruta_x)

    # 2. Impacto en demanda y respaldo con reserva
    datos_y = monitor.percibir_estacion(estacion_y)
    monitor.informar_aumento_aforo_post_retencion(estacion_y, datos_y["aforo"])
    monitor.enviar_alerta_demanda_acumulada(
        estacion_y, datos_y["aforo"], datos_y["tiempo_espera_min"]
    )

    coordinador.reservar_y_despachar_unidad(bus_apoyo_x, ruta_x)
    coordinador.solicitar_coordinacion_apoyo(bus_apoyo_x, ruta_x, estacion_y)
    regulador.confirmar_frecuencia_cubierta(ruta_x, bus_apoyo_x)
