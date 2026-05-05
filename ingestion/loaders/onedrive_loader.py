import os
import requests
from ingestion.loader_registry import register_loader
from clients.ms_graph_client import graph_get
from ingestion.processing.file_processor import process_file, create_document_from_file
from utils.logging import get_logger
from typing import Generator
from llama_index.core import Document

logger = get_logger(__name__)


def fetch_onedrive_files(user_id: str) -> list:
    """
    Haalt bestanden op uit de OneDrive van een gebruiker via de Microsoft Graph API.

    Filtert enkel items die effectieve bestanden zijn en retourneert relevante metadata.

    Args:
        user_id (str): ID van de gebruiker waarvan de OneDrive wordt opgehaald.

    Returns:
        list[dict]: Lijst van bestanden met ID, naam en download URL.
    """
    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root/children"
    res = graph_get(url)

    if res.status_code != 200:
        logger.warning(
            "Fout bij ophalen OneDrive bestanden: %s | %s",
            res.status_code,
            res.text[:300],
        )
        return []

    items = res.json().get("value", [])

    files = []

    for item in items:
        if "file" in item:
            name = item.get("name")

            files.append(
                {
                    "id": item.get("id"),
                    "name": name,
                    "download_url": item.get("@microsoft.graph.downloadUrl"),
                }
            )
            logger.info("OneDrive bestand gevonden: %s", name)

    return files


@register_loader(
    "onedrive",
    schema={
        "user_id": {"type": "string", "required": True},
        "label": {"type": "string", "required": False},
    },
)
def load_onedrive_source(config: dict) -> Generator[Document, None, None]:
    """
    Laadt documenten uit OneDrive en zet deze om naar indexeerbare documenten.

    Deze loader:
    - haalt bestanden uit OneDrive en zet deze om naar indexeerbare documenten.
    - downloadt ze tijdelijk lokaal
    - extraheert de tekstinhoud
    - maakt documenten aan met metadata
    - yieldt deze voor verdere verwerking in de ingest pipeline

    Args:
        config (dict): Configuratie met o.a. user_id en label.

    Yields:
        Document: Verwerkte documenten klaar voor indexering.
    """
    label = config.get("label", "OneDrive")
    user_id = config.get("user_id")

    logger.info("OneDrive loader gestart: %s", label)

    if not user_id:
        logger.warning("Geen user_id opgegeven voor OneDrive")
        return

    files = fetch_onedrive_files(user_id)

    temp_dir = "./temp_onedrive"
    os.makedirs(temp_dir, exist_ok=True)

    for f in files:
        filename = f["name"]
        download_url = f["download_url"]

        if not download_url:
            logger.warning("Geen download URL voor %s", filename)
            continue

        file_path = os.path.join(temp_dir, filename)

        logger.info("Bestand downloaden: %s", filename)

        try:
            res = requests.get(download_url, timeout=30)
            if res.status_code != 200:
                logger.warning("Download mislukt: %s", filename)
                continue

            with open(file_path, "wb") as file:
                file.write(res.content)
        except Exception as e:
            logger.exception("Fout bij downloaden: %s", e)
            continue

        content = process_file(file_path, filename)

        try:
            os.remove(file_path)
            logger.info("Tijdelijk bestand verwijderd: %s", filename)
        except Exception as e:
            logger.warning("Kon tijdelijk bestand niet verwijderen: %s", e)

        if not content.strip():
            logger.warning("Lege content voor %s", filename)
            continue

        metadata = {
            "source": "onedrive",
            "source_type": "onedrive_file",
            "source_id": f["id"],
            "title": filename,
            "filename": filename,
        }

        doc = create_document_from_file(content, metadata)

        if doc:
            yield doc
