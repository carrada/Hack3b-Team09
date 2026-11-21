"""Grafo LangGraph del sistema multiagente.

recepcion ──Send──► especialista_{escrituras,predial,alineamiento,uso_suelo} (paralelo)
                              └──────────► validador_cruzado ──► dictamen ──► [revision_humana] ──► END
"""
from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from .agents.dictamen import nodo_dictamen, nodo_revision_humana
from .agents.especialistas import crear_especialista
from .agents.recepcion import nodo_recepcion
from .agents.validador import nodo_validador_cruzado
from .config import TIPOS
from .schemas import ExpedienteState

NODO_ESP = {t: f"especialista_{t}" for t in TIPOS}


def repartir(state: ExpedienteState):
    """Fan-out: un Send por cada tipo presente. Si no hay ninguno, directo al validador (que corre siempre)."""
    envios = []
    for t in TIPOS:
        docs = [d for d in state.get("documentos", []) if d.get("tipo") == t]
        if docs:
            envios.append(Send(NODO_ESP[t], {"tipo": t, "documentos": docs, "uso_requerido": state["uso_requerido"]}))
    return envios or ["validador_cruzado"]


def tras_dictamen(state: ExpedienteState):
    if state.get("hitl") and state["dictamen"]["requiere_humano"]:
        return "revision_humana"
    return END


def construir_grafo(checkpointer=None):
    g = StateGraph(ExpedienteState)
    g.add_node("recepcion", nodo_recepcion)
    for t in TIPOS:
        g.add_node(NODO_ESP[t], crear_especialista(t))
    g.add_node("validador_cruzado", nodo_validador_cruzado)
    g.add_node("dictamen", nodo_dictamen)
    g.add_node("revision_humana", nodo_revision_humana)

    g.add_edge(START, "recepcion")
    g.add_conditional_edges("recepcion", repartir, [*NODO_ESP.values(), "validador_cruzado"])
    for n in NODO_ESP.values():
        g.add_edge(n, "validador_cruzado")  # join: espera a todos los especialistas del superstep
    g.add_edge("validador_cruzado", "dictamen")
    g.add_conditional_edges("dictamen", tras_dictamen, ["revision_humana", END])
    g.add_edge("revision_humana", END)
    return g.compile(checkpointer=checkpointer or InMemorySaver())


def diagrama_mermaid() -> str:
    return construir_grafo().get_graph().draw_mermaid()
