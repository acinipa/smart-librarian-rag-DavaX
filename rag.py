# rag.py
import os
import re
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

DATA_MD = Path("data/book_summaries.md")
CHROMA_PATH = Path("chroma")
COLLECTION_NAME = "book_summaries"

def parse_books_md(md_text: str) -> List[Dict[str, Any]]:
    """Parse the markdown file into records {id, title, text, metadata}."""
    blocks = re.split(r"^##\s*Title:\s*", md_text, flags=re.MULTILINE)
    records: List[Dict[str, Any]] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # title: up to the first empty line or end of block
        lines = block.splitlines()
        title = lines[0].strip()
        summary = "\n".join(lines[1:]).strip()
        rid = title.lower().replace(" ", "-")
        records.append({
            "id": rid,
            "title": title,
            "text": summary,
            "metadata": {"title": title}
        })
    return records

def get_client() -> chromadb.PersistentClient:
    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PATH))

def get_or_create_collection(client: chromadb.PersistentClient):
    emb_fn = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=emb_fn
    )

def bootstrap_index() -> int:
    """Read data/book_summaries.md and (re)index if the collection is empty. Returns the number of records."""
    client = get_client()
    col = get_or_create_collection(client)
    count = col.count()
    if count and count >= 10:
        return count

    if not DATA_MD.exists():
        raise FileNotFoundError(f"Cannot find {DATA_MD.resolve()}")

    records = parse_books_md(DATA_MD.read_text(encoding="utf-8"))
    # upsert all
    col.upsert(
        ids=[r["id"] for r in records],
        documents=[r["text"] for r in records],
        metadatas=[r["metadata"] for r in records]
    )
    # Chroma automatically persists in PersistentClient;
    # an explicit persist() call is not required,
    # but is safer when running in notebooks.
    try:
        col.persist()
    except Exception:
        pass

    return col.count()

class RAGEngine:
    def __init__(self):
        self.client = get_client()
        self.col = get_or_create_collection(self.client)

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Return the top-k relevant documents (title + text)."""
        out = self.col.query(query_texts=[query], n_results=k)
        results = []
        docs = out.get("documents", [[]])[0]
        metas = out.get("metadatas", [[]])[0]
        ids = out.get("ids", [[]])[0]
        for i, doc in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            title = meta.get("title", ids[i])
            results.append({"title": title, "summary": doc})
        return results
