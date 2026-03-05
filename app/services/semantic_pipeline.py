"""
Semantic pipeline — LangChain chunking + spaCy NER + ChromaDB with enriched metadata.
"""

import logging
import spacy
import chromadb
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# ── spaCy NER model ──────────────────────────────────────────────────────────
nlp = spacy.load("en_core_web_sm")

# ── ChromaDB setup ───────────────────────────────────────────────────────────
chroma_client = chromadb.PersistentClient(path="./chroma_db")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = chroma_client.get_or_create_collection(
    name="agentifyx_solutions",
    embedding_function=sentence_transformer_ef,
)

# ── LangChain splitter ──────────────────────────────────────────────────────
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    separators=["\n\n", "\n", ". ", " ", ""],
)

# NER entity labels we care about
_NER_LABELS = {"ORG", "PRODUCT", "GPE", "PERSON", "WORK_OF_ART", "EVENT"}


# ═════════════════════════════════════════════════════════════════════════════
#  Public API
# ═════════════════════════════════════════════════════════════════════════════

def chunk_and_enrich(parsed_pages: list[dict], source_document: str) -> list[dict]:
    """
    Take structured page dicts from document_parser and produce enriched chunks
    ready for ChromaDB storage.

    Each returned dict has:
        text, page_number, section_title, content_type,
        source_document, chunk_index, extracted_entities
    """
    enriched_chunks: list[dict] = []
    chunk_index = 0

    for page_data in parsed_pages:
        text = page_data.get("text", "")
        if not text.strip():
            continue

        content_type = page_data.get("content_type", "text")
        page_number = page_data.get("page_number", 0)
        section_title = page_data.get("section_title", "")

        # For headings and image_descriptions, keep as single chunks
        if content_type in ("heading", "image_description"):
            entities = _extract_entities(text)
            enriched_chunks.append({
                "text": text,
                "page_number": page_number,
                "section_title": section_title,
                "content_type": content_type,
                "source_document": source_document,
                "chunk_index": chunk_index,
                "extracted_entities": entities,
            })
            chunk_index += 1
            continue

        # Split longer text/table content with LangChain
        sub_chunks = _splitter.split_text(text)

        for sub in sub_chunks:
            entities = _extract_entities(sub)
            enriched_chunks.append({
                "text": sub,
                "page_number": page_number,
                "section_title": section_title,
                "content_type": content_type,
                "source_document": source_document,
                "chunk_index": chunk_index,
                "extracted_entities": entities,
            })
            chunk_index += 1

    return enriched_chunks


def store_embeddings(source_document: str, enriched_chunks: list[dict]) -> int:
    """Store enriched chunks into ChromaDB with full metadata."""
    if not enriched_chunks:
        return 0

    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for chunk in enriched_chunks:
        doc_id = f"{source_document}_chunk_{chunk['chunk_index']}"
        ids.append(doc_id)
        documents.append(chunk["text"])
        metadatas.append({
            "page_number": chunk["page_number"],
            "section_title": chunk["section_title"],
            "content_type": chunk["content_type"],
            "source_document": chunk["source_document"],
            "chunk_index": chunk["chunk_index"],
            # ChromaDB metadata values must be str/int/float/bool
            "extracted_entities": str(chunk.get("extracted_entities", [])),
        })

    # Upsert so re-processing the same file overwrites old chunks
    collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
    return len(documents)


def query_collection(
    query_text: str,
    n_results: int = 5,
    content_type_filter: str | None = None,
    source_filter: str | None = None,
) -> dict:
    """Query ChromaDB with optional metadata filters."""
    where_filter: dict | None = None
    conditions: list[dict] = []

    if content_type_filter:
        conditions.append({"content_type": content_type_filter})
    if source_filter:
        conditions.append({"source_document": source_filter})

    if len(conditions) == 1:
        where_filter = conditions[0]
    elif len(conditions) > 1:
        where_filter = {"$and": conditions}

    kwargs: dict = {
        "query_texts": [query_text],
        "n_results": n_results,
    }
    if where_filter:
        kwargs["where"] = where_filter

    return collection.query(**kwargs)


# ── Legacy wrapper (backward-compat) ────────────────────────────────────────

def chunk_text(text: str, max_chunk_size: int = 800) -> list[str]:
    """Legacy wrapper — splits plain text into chunks."""
    return _splitter.split_text(text)


# ═════════════════════════════════════════════════════════════════════════════
#  Internal helpers
# ═════════════════════════════════════════════════════════════════════════════

def _extract_entities(text: str) -> list[dict]:
    """Run spaCy NER and return matching entities."""
    doc = nlp(text)
    entities: list[dict] = []
    seen: set[str] = set()

    for ent in doc.ents:
        if ent.label_ in _NER_LABELS:
            key = f"{ent.text}|{ent.label_}"
            if key not in seen:
                seen.add(key)
                entities.append({"text": ent.text, "label": ent.label_})

    return entities