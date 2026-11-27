# Mensajes FIPA-ACL del SMA Transcaribe

En la revisión, el profesor pidió que antes de los diagramas de secuencia esté definido cada mensaje con
la estructura FIPA. Su explicación fue esta: primero se construyen y se estructuran los mensajes, que
expresan la intención de comunicación, y después se muestra cómo los agentes los intercambian.

En el código, Gemini solo redacta el texto de `content`. Los demás parámetros los fija el bus de
mensajes (`communication/fipa_acl.py`), así que la estructura no depende del modelo.

## Parámetros comunes

| Parámetro | Valor | Para qué sirve |
|---|---|---|
| `language` | `es` | El contenido va en lenguaje natural, en español |
| `ontology` | `Transcaribe` | Vocabulario compartido: estación, aforo, ruta, bus, reserva, intervalo |
| `protocol` | `FIPA-Inform` o `FIPA-Request` | Inform: un aviso que nadie pidió. Request: una solicitud que exige respuesta |
| `conversation-id` | `cu01-bazurto`, `cu02-t100e`, `cu02-maria-auxiliadora` | Agrupa los mensajes de un mismo escenario |
| `reply-with` | `<conversation-id>-mNN` | Identificador de cada mensaje; es el `[mNN]` de los diagramas |
| `in-reply-to` | id del request que se contesta | Une cada respuesta con su solicitud |

## Inform frente a la respuesta a un request

Esta fue la distinción que hizo el profesor:

- Un **`request`** siempre exige respuesta. Primero llega un `agree` (acepto) o un `refuse` (no puedo). Si
  hubo `agree`, cuando la acción termina se confirma con un `inform-done`. Las tres respuestas llevan
  `in-reply-to`.
- Un **`inform`** es un aviso, por ejemplo la telemetría o una alerta. No contesta a nada y no espera
  respuesta.

Hay que poder explicar un detalle de la norma. `inform-done` no es una performativa distinta: es el
`inform` con el que el protocolo FIPA-Request cierra la acción («ya está hecho»). El código lo etiqueta
`inform-done` para que se lea más claro.

## CU-01: Gestión de congestión, reserva previa y despacho (`conversation-id: cu01-bazurto`)

| Id | Performativa | Emisor → receptor | Contenido (plantilla) | Protocolo | in-reply-to |
|---|---|---|---|---|---|
| m01 | inform | Monitor → Regulador | alerta_congestion(estacion_x, aforo_x, tiempo_espera_x) | FIPA-Inform | — |
| m02 | request | Monitor → Coordinador | reservar_unidad(estacion_x, ruta_x) | FIPA-Request | — |
| m03 | agree | Coordinador → Monitor | reserva_confirmada(bus_reserva_x, codigo_reserva_x) | FIPA-Request | m02 |
| m03′ | refuse | Coordinador → Monitor | reserva_rechazada(estacion_x, sin_unidad_disponible). **La conversación termina** | FIPA-Request | m02 |
| m04 | request | Monitor → Coordinador | despachar_unidad(bus_reserva_x, codigo_reserva_x, ruta_x, estacion_x) | FIPA-Request | — |
| m05 | agree | Coordinador → Monitor | despacho_aceptado(bus_reserva_x, codigo_reserva_x) | FIPA-Request | m04 |
| m06 | request | Coordinador → Regulador | integrar_unidad_ruta(bus_reserva_x, ruta_x, estacion_x) | FIPA-Request | — |
| m07 | request | Regulador → Unidad Vehicular | asignar_recorrido_refuerzo(bus_reserva_x, ruta_x, estacion_x, eta_x) | FIPA-Request | — |
| m08 | request | Unidad Vehicular → Conductor | iniciar_recorrido(bus_reserva_x, estacion_x, ruta_x) | FIPA-Request | — |
| m09 | agree | Conductor → Unidad Vehicular | recorrido_aceptado(bus_reserva_x) | FIPA-Request | m08 |
| m10 | agree | Unidad Vehicular → Regulador | recorrido_aceptado(bus_reserva_x) | FIPA-Request | m07 |
| m11 | agree | Regulador → Coordinador | unidad_integrada(bus_reserva_x, ruta_x) | FIPA-Request | m06 |
| m12 | inform-done | Conductor → Unidad Vehicular | desplazamiento_iniciado(bus_reserva_x, estacion_x) | FIPA-Request | m08 |
| m13 | inform-done | Unidad Vehicular → Regulador | bus_en_ruta(bus_reserva_x, estacion_x) | FIPA-Request | m07 |
| m14 | inform-done | Regulador → Coordinador | refuerzo_activo(bus_reserva_x, ruta_x) | FIPA-Request | m06 |
| m15 | inform-done | Coordinador → Monitor | despacho_completado(bus_reserva_x, estacion_x) | FIPA-Request | m04 |

En la tabla se usan nombres cortos. En los mensajes van los completos: `AgenteMonitorDemandaEstaciones`,
`AgenteCoordinadorOperativoMovilidad`, `AgenteReguladorRutaFrecuencias`, `AgenteUnidadVehicular` y
`AgenteConductor`.

**Ejemplo completo.** Así queda m04 en `trazabilidad_fipa.json`:

```json
{
  "performative": "request",
  "sender": "AgenteMonitorDemandaEstaciones",
  "receiver": "AgenteCoordinadorOperativoMovilidad",
  "content": "Solicito despachar Bus_Reserva_01 con la reserva RES-001 hacia Estacion_Bazurto en la ruta T101.",
  "language": "es",
  "ontology": "Transcaribe",
  "protocol": "FIPA-Request",
  "conversation-id": "cu01-bazurto",
  "reply-with": "cu01-bazurto-m04",
  "in-reply-to": null
}
```

## CU-02: Regulación de frecuencias y respaldo con reserva

### Parte 1, regulación (`conversation-id: cu02-t100e`)

El Regulador calcula el intervalo restando las posiciones (`intervalo_x = posicion_d_x - posicion_x`) y
lo compara con la tolerancia, que va de `intervalo_min` a `intervalo_max` (en el código, de 0,30 a
0,80 km). Según el resultado elige una de tres ramas, que en el diagrama son el `alt`:

- **bajar:** el intervalo es menor que el mínimo y hay riesgo de agrupamiento.
- **subir:** el intervalo es mayor que el máximo y queda un hueco largo.
- **mantener:** el intervalo está dentro de la tolerancia y no se envía ninguna instrucción.

| Id | Performativa | Emisor → receptor | Contenido (plantilla) | Protocolo | in-reply-to |
|---|---|---|---|---|---|
| m01 | inform | Unidad Vehicular → Regulador | reportar_telemetria(bus_delantero_x, ruta_x, posicion_d_x, velocidad_d_x) | FIPA-Inform | — |
| m02 | inform | Unidad Vehicular → Regulador | reportar_telemetria(bus_x, ruta_x, posicion_x, velocidad_x) | FIPA-Inform | — |
| m03 | request | Regulador → Unidad Vehicular | ajustar_marcha(bus_x, accion_x, velocidad_objetivo_x, tiempo_retencion_x, estacion_x), con accion_x ∈ {bajar, subir} | FIPA-Request | — |
| m04 | request | Unidad Vehicular → Conductor | bajar: retener_y_bajar_velocidad(bus_x, tiempo_retencion_x, velocidad_objetivo_x); subir: subir_velocidad(bus_x, velocidad_objetivo_x) | FIPA-Request | — |
| m05 | agree | Conductor → Unidad Vehicular | maniobra_segura_aceptada(bus_x) | FIPA-Request | m04 |
| m06 | agree | Unidad Vehicular → Regulador | instruccion_aceptada(bus_x) | FIPA-Request | m03 |
| m07 | inform-done | Conductor → Unidad Vehicular | bajar: se_detuvo_en_estacion_y_bajo_velocidad(bus_x); subir: subio_velocidad(bus_x) | FIPA-Request | m04 |
| m08 | inform-done | Unidad Vehicular → Regulador | intervalo_restablecido(bus_x, ruta_x) | FIPA-Request | m03 |

¿Por qué el Regulador le escribe a la Unidad Vehicular y no directamente al Conductor? Es el ejemplo del
profesor: «Rafa, dile a Samuel que compre la crispeta».

- El Regulador define el parámetro, es decir, la velocidad objetivo.
- La Unidad Vehicular lo muestra en la consola del bus y le pide al Conductor la acción concreta: «baje la
  velocidad a X» o «retenga en la estación».
- El Conductor es el único que mueve el bus, por eso es él quien confirma que lo hizo (`agree` y después
  `inform-done`).

### Parte 2, respaldo (`conversation-id: cu02-maria-auxiliadora`)

| Id | Performativa | Emisor → receptor | Contenido (plantilla) | Protocolo | in-reply-to |
|---|---|---|---|---|---|
| m01 | inform | Monitor → Regulador | aumento_aforo(estacion_y, aforo_y) | FIPA-Inform | — |
| m02 | inform | Monitor → Coordinador | alerta_demanda_acumulada(estacion_y, aforo_y, tiempo_espera_y) | FIPA-Inform | — |
| m03–m06 | — | Monitor ↔ Coordinador | El mismo protocolo de reserva previa y despacho del CU-01 (m02 a m05), con bus_apoyo_x | FIPA-Request | — |
| m07 | request | Coordinador → Regulador | coordinar_ingreso_apoyo(bus_apoyo_x, ruta_x, estacion_y) | FIPA-Request | — |
| m08 | inform-done | Regulador → Coordinador | frecuencia_cubierta(bus_apoyo_x, ruta_x) | FIPA-Request | m07 |
