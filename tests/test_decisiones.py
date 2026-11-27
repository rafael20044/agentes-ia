"""Pruebas de las reglas de interacción, sin llamar a Gemini.

Cubren las correcciones de la revisión del profesor:
- La reserva es una solicitud aparte del despacho y, si no hay unidad, el Coordinador rechaza y el caso termina.
- El Regulador evalúa el intervalo y decide bajar, subir o mantener (alt).
- Todo mensaje lleva la estructura FIPA-ACL completa.
"""

import pytest

from agents import (
    AgenteConductor,
    AgenteCoordinadorOperativoMovilidad,
    AgenteMonitorDemandaEstaciones,
    AgenteReguladorRutaFrecuencias,
    AgenteUnidadVehicular,
)
from agents.regulador_frecuencias import AccionRegulacion
from communication.fipa_acl import CAMPOS_FIPA, BusMensajesFIPA
from environment.entorno_transcaribe import EntornoUrbanoTranscaribe
from use_cases import ejecutar_cu01, ejecutar_cu02


class LLMFalso:
    """Devuelve la instrucción como contenido, sin red."""

    def generar_json(self, system_prompt: str, instruccion: str) -> dict:
        return {"content": instruccion}


class TrazabilidadEnMemoria:
    def __init__(self):
        self.registros: list[dict] = []

    def registrar(self, msg: dict) -> None:
        self.registros.append(msg)


def armar_sistema(patio_vacio: bool = False):
    entorno = EntornoUrbanoTranscaribe()
    if patio_vacio:
        for datos in entorno.buses.values():
            if datos["ruta"] == "Patio":
                datos["estado"] = "en_mantenimiento"
    traza = TrazabilidadEnMemoria()
    canal = BusMensajesFIPA(llm_client=LLMFalso(), trazabilidad=traza)
    agentes = (
        AgenteMonitorDemandaEstaciones(entorno=entorno, bus=canal),
        AgenteCoordinadorOperativoMovilidad(entorno=entorno, bus=canal),
        AgenteReguladorRutaFrecuencias(entorno=entorno, bus=canal),
        AgenteUnidadVehicular(entorno=entorno, bus=canal),
        AgenteConductor(entorno=entorno, bus=canal),
    )
    return entorno, traza, agentes


def performativas(traza: TrazabilidadEnMemoria) -> list[str]:
    return [m["performative"] for m in traza.registros]


def test_sin_unidad_en_patio_el_coordinador_rechaza_y_el_cu01_termina():
    entorno, traza, agentes = armar_sistema(patio_vacio=True)

    ejecutar_cu01(*agentes)

    assert performativas(traza) == ["inform", "request", "refuse"]
    solicitud, rechazo = traza.registros[1], traza.registros[2]
    assert rechazo["in-reply-to"] == solicitud["reply-with"]
    assert all(b["estado"] != "despachada" for b in entorno.buses.values())


def test_con_unidad_la_reserva_va_antes_del_despacho_y_cita_su_codigo():
    entorno, traza, agentes = armar_sistema()

    ejecutar_cu01(*agentes)

    m = traza.registros
    # inform alerta, request reserva, agree reserva, request despacho, agree despacho
    assert performativas(traza)[:5] == ["inform", "request", "agree", "request", "agree"]
    assert "RES-001" in m[2]["content"] and "Bus_Reserva_01" in m[2]["content"]
    assert "RES-001" in m[3]["content"] and "Bus_Reserva_01" in m[3]["content"]
    # El cierre al Monitor responde a la solicitud de despacho
    assert m[-1]["performative"] == "inform-done"
    assert m[-1]["in-reply-to"] == m[3]["reply-with"]
    assert entorno.buses["Bus_Reserva_01"]["estado"] == "en_ruta"


@pytest.mark.parametrize(
    ("pos_delantero", "pos_trasero", "esperado"),
    [
        ("Km 4.20", "Km 4.08", AccionRegulacion.BAJAR),     # 0.12 km: se están agrupando
        ("Km 5.50", "Km 4.08", AccionRegulacion.SUBIR),     # 1.42 km: hueco largo
        ("Km 4.60", "Km 4.08", AccionRegulacion.MANTENER),  # 0.52 km: dentro de la tolerancia
    ],
)
def test_el_regulador_decide_segun_el_intervalo(pos_delantero, pos_trasero, esperado):
    _, _, (_, _, regulador, _, _) = armar_sistema()

    decision = regulador.decidir_ajuste(
        {"posicion_gps": pos_delantero, "velocidad_kmh": 42},
        {"posicion_gps": pos_trasero, "velocidad_kmh": 48},
    )

    assert decision["accion"] == esperado


def test_si_el_intervalo_esta_en_tolerancia_no_se_le_ordena_nada_al_conductor():
    entorno, traza, agentes = armar_sistema()
    entorno.buses["Bus_T100E_01"]["posicion_gps"] = "Km 4.60"

    ejecutar_cu02(*agentes)

    assert not any(m["receiver"] == "AgenteConductor" for m in traza.registros)
    assert entorno.buses["Bus_T100E_02"]["velocidad_kmh"] == 48


def test_si_hay_hueco_largo_el_conductor_sube_la_velocidad():
    entorno, traza, agentes = armar_sistema()
    entorno.buses["Bus_T100E_01"]["posicion_gps"] = "Km 5.50"

    ejecutar_cu02(*agentes)

    assert entorno.buses["Bus_T100E_02"]["velocidad_kmh"] == 50
    orden = next(m for m in traza.registros if m["receiver"] == "AgenteConductor")
    assert "subir la velocidad" in orden["content"]


def test_todo_mensaje_tiene_la_estructura_fipa_completa():
    _, traza, agentes = armar_sistema()

    ejecutar_cu01(*agentes)
    ejecutar_cu02(*agentes)

    assert traza.registros
    for msg in traza.registros:
        assert set(CAMPOS_FIPA) <= set(msg)
        assert msg["language"] == "es"
        assert msg["ontology"] == "Transcaribe"
        assert msg["conversation-id"].startswith("cu0")
