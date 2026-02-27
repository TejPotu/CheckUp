"""RAG retriever — search Qdrant for relevant health knowledge."""

from __future__ import annotations

import logging

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from checkup.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "models/gemini-embedding-001"
TOP_K = 5


def _get_vector_store() -> QdrantVectorStore:
    """Return a QdrantVectorStore instance (local or remote)."""
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=settings.google_api_key,
    )

    if settings.qdrant_path:
        client = QdrantClient(path=settings.qdrant_path)
    else:
        client = QdrantClient(url=settings.qdrant_url)

    return QdrantVectorStore(
        client=client,
        collection_name=settings.qdrant_collection,
        embedding=embeddings,
    )


async def retrieve_context(query: str, top_k: int = TOP_K) -> list[Document]:
    """Retrieve the most relevant health knowledge chunks for a query.

    Args:
        query: The user's health question (in English).
        top_k: Number of top results to return.

    Returns:
        List of relevant Document objects with page_content and metadata.
    """
    try:
        store = _get_vector_store()
        results = store.similarity_search(query, k=top_k)
        logger.info("Retrieved %d chunks for query: '%s'", len(results), query[:60])
        return results
    except Exception as e:
        logger.error("RAG retrieval failed: %s", e)
        return []
