import os
import requests
import re
from llama_index.core import Document
from markdownify import markdownify as md
import html
from ingestion.preprocessing.cleaning import clean_text, clean_topdesk_text, normalize_text
from ingestion.loader_registry import register_loader
from utils.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)

def html_to_markdown(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = md(raw_html, heading_style="ATX", bullets="-")
    text = html.unescape(text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = normalize_text(text)
    return text


def has_usable_content(item:dict)->bool:
    translation = item.get("translation") or {}
    content = translation.get("content") or {}
    body = (content.get("content") or "").strip()
    return bool(body)

def fetch_topdesk_knowledge_items():
    if not all([settings.TOPDESK_BASE_URL, settings.TOPDESK_USER, settings.TOPDESK_SECRET]):
        logger.error("TOPdesk loader configuratie ontbreekt!")
        return

    url = f"{settings.TOPDESK_BASE_URL}/services/knowledge-base-v1/knowledgeItems"
    params = {
        "start": 0,
        "page_size": 100,
        "language":"nl",
        "fields": "title,description,content,keywords"
    }

    while url:
        r = requests.get(
            url,
            auth=(settings.TOPDESK_USER, settings.TOPDESK_SECRET),
            params=params if "?" not in url else None,
            headers={"Accept": "application/json"},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()

        items = data.get("item", [])

        for item in items:
            if not has_usable_content(item):
                continue

            c = ((item.get("translation") or {}).get("content") or {})
            title = (c.get("title") or "").strip()
            description_md = html_to_markdown(c.get("description") or "")
            content_md = html_to_markdown(c.get("content") or "")
            keywords = (c.get("keywords") or "").strip()

            text_parts = []

            if title:
                text_parts.append(f"Titel: {title}")
            if description_md:
                text_parts.append(f"Beschrijving:\n{description_md}")
            if content_md:
                text_parts.append(f"Inhoud:\n{content_md}")
            if keywords:
                text_parts.append(f"Trefwoorden: {keywords}")

            full_text = "\n\n".join(text_parts).strip()
            if not full_text:
                continue

            meta = {
                "source": "topdesk",
                "source_type": "topdesk_kb",
                "source_id": item.get("id"),
                "number": item.get("number"),
                "title": title
            }

            doc = Document(text=full_text, metadata=meta)
            doc.excluded_embed_metadata_keys = ["source_type", "source_id"]
            doc.excluded_llm_metadata_keys = ["source_type", "source_id"]

            yield doc

        url = data.get("next") or None
        params = None

def fetch_topdesk_incidents(limit=300):
    if not all([settings.TOPDESK_BASE_URL, settings.TOPDESK_USER, settings.TOPDESK_SECRET]):
        logger.error("TOPdesk loader configuratie ontbreekt!")
        return []
    
    url = f"{settings.TOPDESK_BASE_URL}/tas/api/incidents"

    params = {
        "page_size":50,
        "start": 0,
    }
    all_items = []

    while url and len(all_items) < limit:
        r = requests.get(
            url,
            auth=(settings.TOPDESK_USER, settings.TOPDESK_SECRET),
            params=params if "?" not in url else None,
            headers={"Accept": "application/json"},
            timeout=30
        )
        r.raise_for_status()

        data = r.json()

        results = data if isinstance(data, list) else data.get("results",[])
        all_items.extend(results)

        if len(results) < params["page_size"]:
            break
        params["start"] += params["page_size"]

    logger.info("TOPdesk incidents opgehaald: %s (limit: %s)", len(all_items[:limit]), limit)

    return all_items[:limit]

def incidents_to_documents(items: list[dict]) -> list[Document]:
    docs = []

    for item in items:
        description = (item.get("briefDescription") or "").strip()
        request = (item.get("request") or "")
        request = clean_topdesk_text(request)
        request = clean_text(request)
        number = item.get("number")

        if not description and not request:
            continue

        text = f"""
Probleem: {description}
Details:
{request}
""".strip()
        
        meta = {
            "source": "topdesk",
            "source_type": "incident",
            "number": number,
            "source_id": item.get("id")
        }

        doc = Document(text=text, metadata=meta)
        docs.append(doc)

    return docs

@register_loader("topdesk", schema={
    "include_kb": {"type": "bool", "default": True},
    "incident_limit": {"type": "int", "default": 200}

})
def load_topdesk_source(config: dict):
    """Loader voor TOPdesk bronnen.
    Haalt knowledge items op
    """

    include_kb = config.get("include_kb", True)

    try:
        if include_kb:
            count = 0

            for doc in fetch_topdesk_knowledge_items():
                yield doc
                count += 1
            logger.info("TOPdesk kennis-items docs: %s", count)
    
    except Exception as e:
        logger.exception("Fout bij ophalen van TOPdesk data: %s", e)