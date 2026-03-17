"""LangGraph: compile the CheckUp conversation graph."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from checkup.agent.state import ConversationState
from checkup.agent.nodes.router import route
from checkup.agent.nodes.health_qa import health_qa
from checkup.agent.nodes.checkin import checkin
from checkup.agent.nodes.escalation import escalate
from checkup.agent.nodes.register import register
from checkup.language.detector import detect_language
from checkup.language.translator import translate_to_english, translate_response

logger = logging.getLogger(__name__)


# ── Wrapper nodes ──────────────────────────────────────────────────────

async def detect_language_node(state: ConversationState) -> dict[str, Any]:
    """Detect language and translate input to English."""
    original_text = state.get("original_text", "")
    lang = detect_language(original_text)

    english_text = original_text
    if lang == "te":
        english_text = await translate_to_english(original_text)

    return {
        "detected_language": lang,
        "english_text": english_text,
    }


async def respond_node(state: ConversationState) -> dict[str, Any]:
    """Translate the response back to the user's language."""
    response_text = state.get("response_text", "")
    detected_lang = state.get("detected_language", "en")

    final_text = response_text
    if detected_lang == "te":
        final_text = await translate_response(response_text, "te")

    return {"response_text": final_text}


# ── Conditional edge ──────────────────────────────────────────────────

def route_by_intent(state: ConversationState) -> str:
    """Route to the appropriate node based on classified intent."""
    intent = state.get("intent", "health_qa")
    if intent == "escalate":
        return "escalate"
    if intent in ("checkin", "medication"):
        return "checkin"
    if intent == "register":
        return "register"
    return "health_qa"


def should_escalate_after_checkin(state: ConversationState) -> str:
    """After check-in, escalate if risk is high."""
    risk = state.get("risk_level", "low")
    if risk == "high":
        return "escalate"
    return "respond"


# ── Build the graph ───────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Construct and return the CheckUp StateGraph (uncompiled)."""
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("detect_language", detect_language_node)
    graph.add_node("route", route)
    graph.add_node("health_qa", health_qa)
    graph.add_node("checkin", checkin)
    graph.add_node("escalate", escalate)
    graph.add_node("register", register)
    graph.add_node("respond", respond_node)

    # Set entry point
    graph.set_entry_point("detect_language")

    # Edges
    graph.add_edge("detect_language", "route")

    graph.add_conditional_edges("route", route_by_intent, {
        "health_qa": "health_qa",
        "checkin": "checkin",
        "escalate": "escalate",
        "register": "register",
    })

    graph.add_edge("health_qa", "respond")
    graph.add_edge("register", "respond")

    graph.add_conditional_edges("checkin", should_escalate_after_checkin, {
        "escalate": "escalate",
        "respond": "respond",
    })

    graph.add_edge("escalate", "respond")
    graph.add_edge("respond", END)

    return graph


def compile_graph(checkpointer=None):
    """Compile the graph with optional checkpointer for persistence."""
    graph = build_graph()
    return graph.compile(checkpointer=checkpointer)
