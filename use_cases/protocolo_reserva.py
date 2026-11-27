"""Protocolo de reserva y despacho de una unidad de patio (FIPA-Request en dos solicitudes)."""

from agents import AgenteCoordinadorOperativoMovilidad, AgenteMonitorDemandaEstaciones


def reservar_y_despachar(
    monitor: AgenteMonitorDemandaEstaciones,
    coordinador: AgenteCoordinadorOperativoMovilidad,
    estacion: str,
    ruta: str,
) -> tuple[str, str] | None:
    """Devuelve (bus, código de reserva) si la unidad quedó despachada, o None si no hubo reserva."""
    # 1. Solicitud de reserva: el Coordinador evalúa el patio y acepta o rechaza
    monitor.solicitar_reserva_unidad(estacion, ruta)
    reserva = coordinador.evaluar_reserva()
    if reserva is None:
        coordinador.rechazar_reserva(estacion)
        print("[PROTOCOLO] Sin unidad disponible: no hay reserva y la conversación termina aquí.")
        return None
    bus_id, codigo_reserva = reserva
    coordinador.aceptar_reserva(bus_id, codigo_reserva, estacion)

    # 2. Solicitud de despacho: cita el bus y el código de la reserva previa
    monitor.solicitar_despacho(bus_id, codigo_reserva, ruta, estacion)
    coordinador.despachar_unidad(bus_id, ruta, codigo_reserva)
    coordinador.aceptar_despacho(bus_id, codigo_reserva, ruta)
    return bus_id, codigo_reserva
