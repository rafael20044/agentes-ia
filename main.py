"""Punto de entrada y composición de capas del Sistema Multiagente Transcaribe."""

import json

from agents import (
    AgenteConductor,
    AgenteCoordinadorOperativoMovilidad,
    AgenteMonitorDemandaEstaciones,
    AgenteReguladorRutaFrecuencias,
    AgenteUnidadVehicular,
)
from communication.fipa_acl import BusMensajesFIPA
from environment.entorno_transcaribe import EntornoUrbanoTranscaribe
from infrastructure.llm_client import GeminiLLMClient
from infrastructure.traceability_db import BaseDatosTrazabilidad
from use_cases import ejecutar_cu01, ejecutar_cu02


def main() -> None:
    # 1. Capa de Infraestructura
    llm_client = GeminiLLMClient()
    trazabilidad = BaseDatosTrazabilidad()

    # 2. Capa de Comunicación (FIPA-ACL)
    bus_fipa = BusMensajesFIPA(llm_client=llm_client, trazabilidad=trazabilidad)

    # 3. Capa de Entorno Compartido
    entorno = EntornoUrbanoTranscaribe()

    # 4. Capa de Agentes Especializados
    monitor = AgenteMonitorDemandaEstaciones(entorno=entorno, bus=bus_fipa)
    coordinador = AgenteCoordinadorOperativoMovilidad(entorno=entorno, bus=bus_fipa)
    regulador = AgenteReguladorRutaFrecuencias(entorno=entorno, bus=bus_fipa)
    unidad = AgenteUnidadVehicular(entorno=entorno, bus=bus_fipa)
    conductor = AgenteConductor(entorno=entorno, bus=bus_fipa)

    # 5. Capa de Orquestación / Casos de Uso
    ejecutar_cu01(monitor, coordinador, regulador, unidad, conductor)
    ejecutar_cu02(monitor, coordinador, regulador, unidad, conductor)

    print("\n" + "=" * 75)
    print(
        f"SIMULACIÓN COMPLETA | Total mensajes FIPA ACL registrados en BD: "
        f"{trazabilidad.total()}"
    )
    print("Estado final de estaciones:", json.dumps(entorno.estaciones, ensure_ascii=False))
    print("Estado final de flota:", json.dumps(entorno.buses, ensure_ascii=False))


if __name__ == "__main__":
    main()
