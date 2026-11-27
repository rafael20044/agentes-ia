"""Protocolo y bus de mensajería FIPA-ACL."""

from typing import Any

from config.settings import LANGUAGE, ONTOLOGY
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


# Respuestas que, en FIPA-Request, contestan a un request previo
RESPUESTAS_A_REQUEST = {Performativa.AGREE, Performativa.REFUSE, Performativa.INFORM_DONE}
# Respuestas que cierran el request (después de ellas ya no se espera nada más)
RESPUESTAS_FINALES = {Performativa.REFUSE, Performativa.INFORM_DONE}

CAMPOS_FIPA = (
    "performative",
    "sender",
    "receiver",
    "content",
    "language",
    "ontology",
    "protocol",
    "conversation-id",
    "reply-with",
    "in-reply-to",
)


class BusMensajesFIPA:
    """Motor de emisión y trazabilidad de mensajes FIPA-ACL entre agentes.

    Gemini solo redacta el `content`. Los demás parámetros del mensaje los fija el bus,
    para que la estructura FIPA-ACL no dependa de lo que responda el modelo.
    """

    def __init__(
        self,
        llm_client: GeminiLLMClient,
        trazabilidad: BaseDatosTrazabilidad,
        ontology: str = ONTOLOGY,
        language: str = LANGUAGE,
    ):
        self._llm_client = llm_client
        self._trazabilidad = trazabilidad
        self._ontology = ontology
        self._language = language
        self._conversation_id = "sin-conversacion"
        self._contador = 0
        # Requests abiertos: (quien pidió, a quién le pidió) -> reply-with del request
        self._requests_abiertos: dict[tuple[str, str], str] = {}

    def iniciar_conversacion(self, conversation_id: str) -> None:
        """Agrupa los mensajes siguientes bajo un mismo conversation-id (un escenario)."""
        self._conversation_id = conversation_id
        self._contador = 0
        self._requests_abiertos.clear()

    def emitir(
        self,
        sender: str,
        receiver: str,
        performative: str,
        protocol: str,
        instruccion: str,
    ) -> dict[str, Any]:
        self._contador += 1
        reply_with = f"{self._conversation_id}-m{self._contador:02d}"
        in_reply_to = self._resolver_in_reply_to(sender, receiver, performative)

        # Prompt de sistema: el LLM redacta el contenido dentro de la estructura FIPA-ACL
        system_prompt = (
            f"Eres el agente '{sender}' del Sistema Multiagente de Transcaribe. "
            "Responde UNICAMENTE con un objeto JSON válido que siga el estándar FIPA ACL "
            "con exactamente estas llaves: performative, sender, receiver, content, language, "
            "ontology, protocol, conversation-id. "
            f"Usa performative='{performative}', sender='{sender}', receiver='{receiver}', "
            f"language='{self._language}', ontology='{self._ontology}', protocol='{protocol}', "
            f"conversation-id='{self._conversation_id}'. "
            "IMPORTANTE: El valor de la llave 'content' debe ser SIEMPRE una oración clara en texto plano "
            "en español y NUNCA un objeto JSON ni un string con JSON escapado adentro."
        )
        generado = self._llm_client.generar_json(system_prompt=system_prompt, instruccion=instruccion)

        msg: dict[str, Any] = {
            "performative": performative,
            "sender": sender,
            "receiver": receiver,
            "content": str(generado.get("content", instruccion)),
            "language": self._language,
            "ontology": self._ontology,
            "protocol": protocol,
            "conversation-id": self._conversation_id,
            "reply-with": reply_with,
            "in-reply-to": in_reply_to,
        }
        if performative == Performativa.REQUEST:
            self._requests_abiertos[(sender, receiver)] = reply_with

        self._trazabilidad.registrar(msg)
        return msg

    def _resolver_in_reply_to(self, sender: str, receiver: str, performative: str) -> str | None:
        # Una respuesta (agree, refuse, inform-done) contesta al último request que le hizo el receptor
        if performative not in RESPUESTAS_A_REQUEST:
            return None
        clave = (receiver, sender)
        if performative in RESPUESTAS_FINALES:
            return self._requests_abiertos.pop(clave, None)
        return self._requests_abiertos.get(clave)
