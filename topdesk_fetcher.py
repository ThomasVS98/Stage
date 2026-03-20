import os
import requests
import re
from llama_index.core import Document
from markdownify import markdownify as md
import html
from dotenv import load_dotenv

load_dotenv()

TOPDESK_BASE_URL = os.getenv("TOPDESK_BASE_URL")
TOPDESK_USER = os.getenv("TOPDESK_USER")
TOPDESK_SECRET = os.getenv("TOPDESK_SECRET")

def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+\n", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def html_to_markdown(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = md(raw_html, heading_style="ATX", bullets="-")
    text = html.unescape(text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = normalize_text(text)
    return text


def has_usable_content(item:dict)->bool:
    body = (((item.get("translation") or {}).get("content") or {}).get("content") or "").strip()
    return bool(body)

def fetch_topdesk_knowledge_items():
    url = f"{TOPDESK_BASE_URL}/services/knowledge-base-v1/knowledgeItems"
    params = {
        "start": 0,
        "page_size": 100,
        "language":"nl",
        "fields": "title,description,content,keywords"
    }

    all_items = []

    while url:
        r = requests.get(
            url,
            auth=(TOPDESK_USER,TOPDESK_SECRET),
            params=params if "?" not in url else None,
            headers={"Accept": "application/json"},
            timeout=30
        )
        r.raise_for_status()
        data = r.json()

        all_items.extend(data.get("item", [] ))
        url = data.get("next") or None
        params = None

    usable = [i for i in all_items if has_usable_content(i)]

    return usable

def topdesk_items_to_documents(items:list[dict]) -> list[Document]:
    
    docs = []

    for item in items:
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
            "number": item.get("number")
        }

        doc = Document(text=full_text, metadata=meta)
        doc.excluded_embed_metadata_keys = ["source_type","source_id"]
        doc.excluded_llm_metadata_keys = ["source_type","source_id"]
        docs.append(doc)

    return docs

def fetch_topdesk_documents():
    items = fetch_topdesk_knowledge_items()
    return topdesk_items_to_documents(items)

# if __name__ == "__main__":
#     items = fetch_topdesk_knowledge_items()
#     docs = topdesk_items_to_documents(items)

#     target = next((i for i in items if i.get("number") == "KI 0160"), None)

#     if not target:
#         print("KI 0160 niet gevonden")
#     else:
#         body = (((target.get("translation") or {}).get("content") or {}).get("content") or "")
#         print("\n=== VOLLEDIGE INHOUD KI 0160 ===\n")
#         print(body)  # volledig, niet afgekapt

#     converted = html_to_markdown(body)

#     print("\n=== GECONVERTEERDE TEKST KI 0160 ===\n")
#     print(converted)

#     with open("ki_0160_full.md", "w", encoding="utf-8") as f:
#         f.write(converted)
#     print("Geschreven naar ki_0160_full.md")