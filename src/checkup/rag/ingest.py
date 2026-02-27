"""RAG ingestion pipeline — chunk, embed, and store health documents."""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from checkup.config import settings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "models/embedding-001"
VECTOR_DIMENSION = 768  # dimension for embedding-001


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Return the embedding model."""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=settings.google_api_key,
    )


def get_qdrant_client() -> QdrantClient:
    """Return a Qdrant client."""
    return QdrantClient(url=settings.qdrant_url)


async def ingest_documents(data_dir: str | Path = "data/knowledge") -> int:
    """Load documents from data_dir, split, embed, and store in Qdrant.

    Returns:
        Number of chunks ingested.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.warning("Data directory %s does not exist, skipping ingestion", data_path)
        return 0

    # Load .md files
    loader = DirectoryLoader(
        str(data_path),
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    logger.info("Loaded %d documents from %s", len(documents), data_path)

    if not documents:
        return 0

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(documents)
    logger.info("Split into %d chunks", len(chunks))

    # Ensure Qdrant collection exists
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in collections:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_DIMENSION, distance=Distance.COSINE),
        )
        logger.info("Created Qdrant collection '%s'", settings.qdrant_collection)

    # Embed and store
    embeddings = get_embeddings()
    QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        url=settings.qdrant_url,
        collection_name=settings.qdrant_collection,
    )
    logger.info("Ingested %d chunks into Qdrant", len(chunks))

    return len(chunks)
