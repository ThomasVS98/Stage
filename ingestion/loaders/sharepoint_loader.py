import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import html
import urllib.parse
from markdownify import markdownify as md
from ingestion.preprocessing.cleaning import normalize_text
from utils.logging import get_logger

load_dotenv()
logger = get_logger(__name__)

CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET")
TENANT_ID = os.getenv("SHAREPOINT_TENANT_ID")
LMS_SITE_ID = os.getenv("LMS_SITE_ID")
SERVICE_CATALOG_ID = os.getenv("SERVICE_CATALOG_ID")

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
            href = f"https://stagetm.sharepoint.com{href}"
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

def get_headers():
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    token = requests.post(token_url, data=token_data).json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

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
    logger.info("Ophalen Sharepoint pagina's van site: %s", site_label)
    headers = get_headers()

    pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages"
    res_pages = requests.get(pages_url, headers=headers)

    final_data = []
    if res_pages.status_code != 200:
            logger.warning("Error in ophalen SharePoint pagina's: %s", res_pages.status_code)
            return []
    pages = res_pages.json().get('value', [])
    for page in pages:
        page_id = page.get('id')
        title = page.get('title')
        url = page.get('webUrl')

        content_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages/{page_id}/microsoft.graph.sitePage?$expand=canvasLayout"
        res_content = requests.get(content_url, headers=headers)

        full_page_text = ""

        if res_content.status_code == 200:
            page_details = res_content.json()
            content_parts, all_links = extract_page_content(page_details)
            full_page_text = title + "\n\n" + "\n\n".join(content_parts)

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
    logger.info("Ophalen Sharepoint bestanden van site: %s", site_label)
    headers = get_headers()

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
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
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
        res = requests.get(download_url)
        if res.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(res.content)
            return True
        return False
    except Exception as e:
        logger.exception("Fout bij downloaden: %s", e)
        return False