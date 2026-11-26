"""Caso de Uso 1 (CU-01): Gestión de congestión, reserva de flota y despacho a estación."""

from agents import (
    AgenteConductor,
    AgenteCoordinadorOperativoMovilidad,
    AgenteMonitorDemandaEstaciones,
    AgenteReguladorRutaFrecuencias,
    AgenteUnidadVehicular,
)


def ejecutar_cu01(
    monitor: AgenteMonitorDemandaEstaciones,
    coordinador: AgenteCoordinadorOperativoMovilidad,
    regulador: AgenteReguladorRutaFrecuencias,
    unidad: AgenteUnidadVehicular,
    conductor: AgenteConductor,
) -> None:
    print("\n" + "=" * 75)
    print("CU-01: GESTIÓN DE CONGESTIÓN, RESERVA DE FLOTA Y DESPACHO A ESTACIÓN")
    print("=" * 75)

    # Escenario sobre la troncal T101 en Estación Bazurto
    estacion_x = "Estacion_Bazurto"
    ruta_x = "T101"
    bus_reserva_x = "Bus_Reserva_01"

    # 1. Percepción del entorno y detección de saturación
    datos = monitor.percibir_estacion(estacion_x)
    if not monitor.detectar_saturacion(datos):
        print("Aforo dentro de parámetros normales.")
        return

    monitor.notificar_alerta_congestion(
        estacion_x, datos["aforo"], datos["tiempo_espera_min"]
    )
    monitor.solicitar_refuerzo(estacion_x, ruta_x)

    # 2. Reserva y posterior despacho desde patio
    coordinador.reservar_y_despachar_unidad(bus_reserva_x, ruta_x)
    coordinador.confirmar_reserva_y_despacho(bus_reserva_x, estacion_x)

    # 3. Integración a ruta y ejecución a bordo
    coordinador.solicitar_integracion_ruta(bus_reserva_x, ruta_x, estacion_x)
    eta_x = regulador.predecir_eta(bus_reserva_x, estacion_x)
    regulador.asignar_recorrido_refuerzo(bus_reserva_x, ruta_x, estacion_x, eta_x)
    unidad.solicitar_inicio_recorrido_conductor(bus_reserva_x, estacion_x, ruta_x)

    # Cadena de aceptación (AGREE)
    conductor.aceptar_recorrido(bus_reserva_x)
    unidad.confirmar_recorrido_aceptado(bus_reserva_x)
    regulador.confirmar_unidad_integrada(bus_reserva_x, ruta_x)

    # 4. Ejecución física en entorno y cierre en cadena (INFORM-DONE)
    conductor.ejecutar_desplazamiento(bus_reserva_x, estacion_x)
    unidad.informar_unidad_en_ruta(bus_reserva_x, estacion_x)
    regulador.informar_refuerzo_activo(bus_reserva_x, ruta_x)
    coordinador.confirmar_despacho_completado(bus_reserva_x, estacion_x)
