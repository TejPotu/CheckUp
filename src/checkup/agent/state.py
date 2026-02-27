"""Conversation state schema for the LangGraph agent."""

from __future__ import annotations

from typing import Annotated, Optional

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict


class ConversationState(TypedDict):
    """Typed state flowing through every node in the CheckUp graph.

    Attributes:
        messages: Full conversation history (auto-appended via reducer).
        user_phone: Parent's WhatsApp phone number (E.164).
        detected_language: Detected language code — "te" (Telugu) or "en" (English).
        original_text: Raw incoming message text.
        english_text: Message translated to English for LLM processing.
        intent: Classified intent after routing.
        parent_profile_id: FK to parent_profiles table (if registered).
        rag_context: Retrieved knowledge chunks for health Q&A.
        health_summary: Latest check-in data (symptoms, vitals, mood).
        risk_level: Assessed risk — "low", "medium", or "high".
        response_text: Final response to send back (in user's language).
        caregiver_alert: If set, message to send to the caregiver.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    user_phone: str
    detected_language: str
    original_text: str
    english_text: str
    intent: str
    parent_profile_id: Optional[int]
    rag_context: Optional[str]
    health_summary: Optional[dict]
    risk_level: Optional[str]
    response_text: str
    caregiver_alert: Optional[str]
