"""Content Ingestion Pipeline for Ilm Academy:
1. Transcribe lesson videos with OpenAI Whisper (with segment timestamps).
2. Extract text from PowerPoint slides (.pptx) and PDF lecture notes (.pdf).
3. Index all chunks with metadata into ChromaDB using SentenceTransformer embeddings.
"""

import json
from pathlib import Path
from typing import Any

import chromadb
import fitz  # PyMuPDF
import whisper
from pptx import Presentation
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"


def transcribe_videos(
    videos_dir: Path = RAW_DIR / "videos",
    model_name: str = "tiny",
) -> list[dict[str, Any]]:
    """Transcribe all video/audio files with Whisper and return timestamped segments."""
    model = whisper.load_model(model_name)
    transcripts: list[dict[str, Any]] = []

    media_files = sorted(
        p for p in videos_dir.iterdir() if p.suffix.lower() in {".mp4", ".wav", ".mp3", ".m4a"}
    )
    for media_path in media_files:
        lesson_id = media_path.stem
        result = model.transcribe(str(media_path), fp16=False)
        for seg in result.get("segments", []):
            text = seg["text"].strip()
            if not text:
                continue
            transcripts.append(
                {
                    "id": f"{lesson_id}_vid_{seg['id']}",
                    "lesson_id": lesson_id,
                    "source_type": "video_transcript",
                    "source_file": media_path.name,
                    "start_sec": round(float(seg["start"]), 2),
                    "end_sec": round(float(seg["end"]), 2),
                    "text": text,
                }
            )
    return transcripts


def extract_slides(slides_dir: Path = RAW_DIR / "slides") -> list[dict[str, Any]]:
    """Extract text per slide from all .pptx files."""
    slide_chunks: list[dict[str, Any]] = []
    for pptx_path in sorted(slides_dir.glob("*.pptx")):
        lesson_id = pptx_path.stem
        prs = Presentation(str(pptx_path))
        for idx, slide in enumerate(prs.slides, start=1):
            parts = []
            for shape in slide.shapes:
                if shape.has_text_frame:
                    txt = shape.text_frame.text.strip()
                    if txt:
                        parts.append(txt)
            combined = " | ".join(parts)
            if combined:
                slide_chunks.append(
                    {
                        "id": f"{lesson_id}_slide_{idx}",
                        "lesson_id": lesson_id,
                        "source_type": "slide",
                        "source_file": pptx_path.name,
                        "slide_num": idx,
                        "text": combined,
                    }
                )
    return slide_chunks


def extract_notes(notes_dir: Path = RAW_DIR / "notes") -> list[dict[str, Any]]:
    """Extract text per page from all .pdf lecture notes."""
    note_chunks: list[dict[str, Any]] = []
    for pdf_path in sorted(notes_dir.glob("*.pdf")):
        lesson_id = pdf_path.stem
        doc = fitz.open(str(pdf_path))
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                note_chunks.append(
                    {
                        "id": f"{lesson_id}_note_{page_num}",
                        "lesson_id": lesson_id,
                        "source_type": "lecture_note",
                        "source_file": pdf_path.name,
                        "page_num": page_num,
                        "text": text,
                    }
                )
        doc.close()
    return note_chunks


def index_in_chromadb(
    chunks: list[dict[str, Any]],
    chroma_dir: Path = CHROMA_DIR,
    collection_name: str = "ilm_academy_content",
    embed_model_name: str = "all-MiniLM-L6-v2",
) -> chromadb.Collection:
    """Embed and upsert all content chunks into a persistent ChromaDB collection."""
    chroma_dir.mkdir(parents=True, exist_ok=True)
    embedder = SentenceTransformer(embed_model_name)
    client = chromadb.PersistentClient(path=str(chroma_dir))

    # Recreate collection cleanly for deterministic indexing
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts, show_progress_bar=False).tolist()
    ids = [c["id"] for c in chunks]
    metadatas = []
    for c in chunks:
        meta = {
            "lesson_id": c["lesson_id"],
            "source_type": c["source_type"],
            "source_file": c["source_file"],
        }
        if "start_sec" in c:
            meta["start_sec"] = c["start_sec"]
            meta["end_sec"] = c["end_sec"]
        if "slide_num" in c:
            meta["slide_num"] = c["slide_num"]
        if "page_num" in c:
            meta["page_num"] = c["page_num"]
        metadatas.append(meta)

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return collection


def query_content(
    query_text: str,
    top_k: int = 5,
    chroma_dir: Path = CHROMA_DIR,
    collection_name: str = "ilm_academy_content",
    embed_model_name: str = "all-MiniLM-L6-v2",
) -> list[dict[str, Any]]:
    """Semantic search over indexed transcripts, slides, and notes."""
    embedder = SentenceTransformer(embed_model_name)
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collection = client.get_collection(collection_name)
    q_emb = embedder.encode([query_text], show_progress_bar=False).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=top_k)

    hits = []
    for doc, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        hits.append({"score": round(1 - dist, 4), "metadata": meta, "text": doc})
    return hits


def run_ingestion() -> dict[str, int]:
    """Execute full content ingestion pipeline and persist processed JSON + ChromaDB."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/4] Transcribing lesson videos with Whisper...")
    transcripts = transcribe_videos()
    (PROCESSED_DIR / "transcripts.json").write_text(
        json.dumps(transcripts, indent=2), encoding="utf-8"
    )

    print("[2/4] Extracting PowerPoint slides...")
    slides = extract_slides()
    (PROCESSED_DIR / "slides.json").write_text(
        json.dumps(slides, indent=2), encoding="utf-8"
    )

    print("[3/4] Extracting PDF lecture notes...")
    notes = extract_notes()
    (PROCESSED_DIR / "notes.json").write_text(
        json.dumps(notes, indent=2), encoding="utf-8"
    )

    all_chunks = transcripts + slides + notes
    print(f"[4/4] Indexing {len(all_chunks)} chunks into ChromaDB...")
    collection = index_in_chromadb(all_chunks)

    summary = {
        "transcript_segments": len(transcripts),
        "slides": len(slides),
        "notes": len(notes),
        "total_indexed": collection.count(),
    }
    print("Ingestion complete:", summary)
    return summary


if __name__ == "__main__":
    run_ingestion()
    print("\nSample semantic query: 'How do I avoid infinite loops?'")
    for hit in query_content("How do I avoid infinite loops?", top_k=3):
        print(f"  [{hit['score']}] ({hit['metadata']}) {hit['text'][:100]}...")
