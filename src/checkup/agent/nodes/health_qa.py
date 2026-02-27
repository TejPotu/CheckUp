"""Health Q&A node — answers health questions using RAG."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from checkup.agent.state import ConversationState
from checkup.config import settings
from checkup.rag.retriever import retrieve_context

logger = logging.getLogger(__name__)

HEALTH_QA_SYSTEM_PROMPT = """\
You are a compassionate health information assistant for elderly individuals.
You help elderly parents understand their health concerns in simple, clear language.

RULES:
1. Answer based ONLY on the provided context. If the context doesn't cover the question, say so.
2. Use simple language — the response will be translated to Telugu for an elderly person.
3. Be warm and reassuring, but honest.
4. For serious symptoms (chest pain, sudden weakness, difficulty breathing, etc.), ALWAYS advise seeking immediate medical attention.
5. End with: "⚠️ This is general health information, not medical advice. Please consult your doctor for personalized guidance."
6. Keep responses concise — max 3-4 short paragraphs.

CONTEXT:
{context}
"""


async def health_qa(state: ConversationState) -> dict[str, Any]:
    """Answer a health question using RAG retrieval + LLM generation."""
    english_text = state.get("english_text", "")

    # Retrieve relevant health knowledge
    context = await retrieve_context(english_text)
    rag_context = "\n\n".join([doc.page_content for doc in context]) if context else "No relevant information found."

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.google_api_key,
        temperature=0.3,
    )

    response = await llm.ainvoke([
        {"role": "system", "content": HEALTH_QA_SYSTEM_PROMPT.format(context=rag_context)},
        {"role": "user", "content": english_text},
    ])

    answer = response.content.strip()
    logger.info("Health Q&A generated response (%d chars)", len(answer))

    return {
        "rag_context": rag_context,
        "response_text": answer,
        "messages": [AIMessage(content=answer)],
    }
