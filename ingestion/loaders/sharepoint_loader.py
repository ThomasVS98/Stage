import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import html
import urllib.parse
from markdownify import markdownify as md
from ingestion.preprocessing.cleaning import normalize_text
from ingestion.loader_registry import register_loader
from llama_index.core import Document
from ingestion.processing.file_processor import process_file, create_document_from_file
from utils.logging import get_logger
from clients.ms_graph_client import graph_get

load_dotenv()
logger = get_logger(__name__)

SHAREPOINT_BASE_URL = os.getenv("SHAREPOINT_BASE_URL")

def html_to_markdown(raw_html:str):
    if not raw_html:
        return "", []
    
    soup = BeautifulSoup(raw_html, "html.parser")
    related_links = []

    for tag in soup(["script", "style"]):
        tag.decompose()

    for a in soup.find_all("a",href=True):
        href = urllib.parse.unquote(a["href"])
        if href.startswith("/"):
            href = f"{SHAREPOINT_BASE_URL}{href}"
        if not href.startswith("javascript:"):
            related_links.append({
                "title": a.get_text(strip=True),
                "url": href,
            })
            a["href"] = href

    text = md(str(soup), heading_style="ATX", bullets="-")
    text = html.unescape(text)
    text = normalize_text(text)
    return text, related_links

def extract_page_content(page_details):
    content_parts = []
    all_links = []

    layout = page_details.get("canvasLayout", {})
    sections = layout.get("horizontalSections", [])

    for section in sections:
        for column in section.get("columns", []):
            for webpart in column.get("webparts", []):
                raw_html = webpart.get("innerHtml")

                if not raw_html:
                    data = webpart.get("data", {})
                    raw_html = data.get("innerHTML") or data.get("innerHtml") or data.get("text")
                                
                if raw_html:
                    text, links = html_to_markdown(raw_html)
                    content_parts.append(text)
                    all_links.extend(links)

    return content_parts, all_links

def build_folder_url(site_id, folder_id):
    if folder_id == "root":
        return f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root/children"
    return f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{folder_id}/children"

def fetch_all_sharepoint_pages(site_id, site_label):

    pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages"
    res_pages = graph_get(pages_url)

    final_data = []
    if res_pages.status_code != 200:
            logger.warning("Error in ophalen SharePoint pagina's: %s | %s", res_pages.status_code, res_pages.text[:300])
            return []
    pages = res_pages.json().get('value', [])
    for page in pages:
        page_id = page.get('id')
        title = page.get('title')
        url = page.get('webUrl')

        content_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}/microsoft.graph.sitePage?$expand=canvasLayout"
        res_content = graph_get(content_url)

        full_page_text = ""

        if res_content.status_code == 200:
            page_details = res_content.json()
            content_parts, all_links = extract_page_content(page_details)
            full_page_text = title + "\n\n" + "\n\n".join(content_parts)
            if not full_page_text:
                continue

        final_data.append({
            "content": full_page_text.strip(),
            "metadata": {
            "source": "sharepoint",
            "source_id": page_id,
            "title": title,
            "url": url,
            "doc_type": "webpage",
            "site_label": site_label,
        }
        })
        logger.info("Opgehaalde site: %s", title)

    return final_data
    
def fetch_sharepoint_files(site_id, site_label):

    final_files = []
    folders_to_process = ["root"]
    visited_folders = set()
    seen_files = set()

    while folders_to_process:
        current_folder = folders_to_process.pop(0)

        if current_folder in visited_folders:
            continue
        visited_folders.add(current_folder)
        url = build_folder_url(site_id, current_folder)
        res = graph_get(url)
        if res.status_code != 200:
            logger.warning("Graph call mislukt voor files: %s | %s", res.status_code, res.text[:300])
            continue
        items = res.json().get("value", [])
        for item in items:
            if "folder" in item:
                folders_to_process.append(item["id"])
            elif "file" in item:
                file_id = item["id"]
                if file_id in seen_files:
                    continue
                seen_files.add(file_id)
                name = item["name"]
                if name.lower().endswith((".pdf", ".docx", ".xlsx", ".pptx",".txt")):
                    final_files.append({
                        "content": "",  # Wordt gevuld na het downloaden/lezen
                        "metadata": {
                            "source": "sharepoint",
                            "source_id": item["id"],
                            "title": name,
                            "filename": name,
                            "url": item.get("webUrl"),
                            "download_url": item.get("@microsoft.graph.downloadUrl"),
                            "doc_type": "file",
                            "site_label": site_label
                        }
                    })
                    logger.info("Bestand gevonden: %s", name)
    return final_files

def download_sharepoint_file(download_url, save_path):
    """Download een bestand van SharePoint naar een lokale map."""
    try:
        res = requests.get(download_url, timeout=30)
        if res.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(res.content)
            return True
        return False
    except Exception as e:
        logger.exception("Fout bij downloaden: %s", e)
        return False
    
@register_loader("sharepoint", schema={
    "site_id": {"type": "string", "required": True},
    "label": {"type": "string", "required": False}
})
def load_sharepoint_source(config: dict):
    """
    Nieuwe generieke loader voor SharePoint kennisbronnen.
    Gebruikt config ipv hardcoded env variabelen.
    """

    site_id = config.get("site_id")
    label = config.get("label", "SharePoint")

    if not site_id:
        logger.warning("Geen site_id gevonden in config voor SharePoint bron")
        return #[]
    
    #docs = []

    logger.info("SharePoint pagina's ophalen: %s", label)
    pages = fetch_all_sharepoint_pages(site_id, label)

    for page in pages:
        full_text = page["content"]

        new_doc = Document(
            text=full_text,
            metadata=page["metadata"]
        )

        new_doc.metadata["source_type"] = "sharepoint_page"
        new_doc.excluded_embed_metadata_keys = ["url","source_id"]
        new_doc.excluded_llm_metadata_keys = ["url", "source_id"]
        
        #docs.append(new_doc)
        yield new_doc

    logger.info("SharePoint bestanden ophalen: %s", label)
    files = fetch_sharepoint_files(site_id, label)

    temp_dir = "./temp_sharepoint"
    os.makedirs(temp_dir, exist_ok=True)

    for file in files:
        meta = file["metadata"]
        filename = meta["filename"]
        dl_url = meta["download_url"]
        if not dl_url:
            logger.warning("Geen download URL voor bestand: %s", filename)
            continue
        file_path = os.path.join(temp_dir, filename)

        logger.info("Downloaden: %s...", filename)

        if not download_sharepoint_file(dl_url, file_path):
            logger.warning("Download mislukt: %s", filename)
            continue

        full_content = process_file(file_path, filename)
        try:
            os.remove(file_path)
        except Exception as e:
            logger.exception("Fout bij verwijderen tijdelijk bestand %s: %s", filename, e)

        new_doc = create_document_from_file(full_content, meta)
        
        if new_doc:
            #docs.append(new_doc)
            yield new_doc
    
    #logger.info("SharePoint docs totaal: %s", len(docs))

    #return docs