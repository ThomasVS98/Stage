from llama_index.core import Document
from ingestion.preprocessing.cleaning import clean_text, clean_markdown
from llama_index.core import SimpleDirectoryReader
from utils.logging import get_logger
import subprocess
import tempfile
import os
import sys
from pathlib import Path

logger = get_logger(__name__)


def create_document_from_file(content: str, metadata: dict):
    if not content.strip():
        return None

    clean_meta = metadata.copy()
    clean_meta.pop("download_url", None)

    new_doc = Document(text=content, metadata=clean_meta)

    new_doc.metadata.setdefault("source_type", "file")
    new_doc.excluded_embed_metadata_keys = ["url", "download_url", "source_id"]
    new_doc.excluded_llm_metadata_keys = ["url", "source_id", "filename"]

    return new_doc


def process_file(file_path: str, filename: str) -> str:
    try:
        if filename.lower().endswith((".pdf", ".docx")):
            with tempfile.NamedTemporaryFile(
                delete=False, mode="w+", encoding="utf-8"
            ) as tmp:
                tmp_path = tmp.name

            worker_path = (
                Path(__file__).resolve().parent.parent
                / "preprocessing"
                / "docling_worker.py"
            )
            logger.info("Aanroepen worker: %s", worker_path)
            try:
                subprocess.run(
                    [sys.executable, str(worker_path), str(file_path), str(tmp_path)],
                    check=True,
                    cwd=str(Path.cwd()),
                    env={**os.environ, "PYTHONPATH": str(Path.cwd())},
                )
                with open(tmp_path, "r", encoding="utf-8") as f:
                    full_content = f.read()
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        logger.warning(
                            "Kon tijdelijk bestand niet verwijderen: %s", tmp_path
                        )
            # full_content = extract_with_docling(file_path)
            full_content = clean_markdown(full_content)
            full_content = clean_text(full_content)

        else:
            reader = SimpleDirectoryReader(input_files=[file_path])
            file_docs = reader.load_data()
            full_content = "\n\n".join([d.text for d in file_docs])
            full_content = clean_text(full_content)

        return full_content
    except Exception as e:
        logger.exception("Fout bij verwerken bestand %s: %s", filename, e)
        return ""
