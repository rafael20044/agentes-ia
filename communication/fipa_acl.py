"""Protocolo y bus de mensajería FIPA-ACL."""

from typing import Any

from config.settings import ONTOLOGY
from infrastructure.llm_client import GeminiLLMClient
from infrastructure.traceability_db import BaseDatosTrazabilidad


class Performativa:
    # Intenciones comunicativas usadas en los protocolos FIPA-Inform y FIPA-Request
    INFORM = "inform"
    REQUEST = "request"
    AGREE = "agree"
    REFUSE = "refuse"
    INFORM_DONE = "inform-done"


class ProtocoloFIPA:
    INFORM = "FIPA-Inform"
    REQUEST = "FIPA-Request"


class BusMensajesFIPA:
    """Motor de emisión y trazabilidad de mensajes FIPA-ACL entre agentes."""

    def __init__(
        self,
        llm_client: GeminiLLMClient,
        trazabilidad: BaseDatosTrazabilidad,
        ontology: str = ONTOLOGY,
    ):
        self._llm_client = llm_client
        self._trazabilidad = trazabilidad
        self._ontology = ontology

    def emitir(
        self,
        sender: str,
        receiver: str,
        performative: str,
        protocol: str,
        instruccion: str,
    ) -> dict[str, Any]:
        # Prompt de sistema que obliga al LLM a cumplir las 6 llaves del estándar FIPA-ACL
        system_prompt = (
            f"Eres el agente '{sender}' del Sistema Multiagente de Transcaribe. "
            "Responde UNICAMENTE con un objeto JSON válido que siga el estándar FIPA ACL "
            "con exactamente estas llaves: performative, sender, receiver, content, ontology, protocol. "
            f"Usa performative='{performative}', sender='{sender}', receiver='{receiver}', "
            f"ontology='{self._ontology}', protocol='{protocol}'. "
            "IMPORTANTE: El valor de la llave 'content' debe ser SIEMPRE una oración clara en texto plano "
            "en español y NUNCA un objeto JSON ni un string con JSON escapado adentro."
        )
        msg = self._llm_client.generar_json(system_prompt=system_prompt, instruccion=instruccion)
        self._trazabilidad.registrar(msg)
        return msg
