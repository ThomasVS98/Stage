from urllib.parse import urlparse
import re
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from ingestion.preprocessing.cleaning import normalize_text
from utils.logging import get_logger

logger = get_logger(__name__)

def scrape_page(url: str) -> str:
    try:
        res = requests.get(
            url, 
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )
        if res.status_code != 200:
            logger.warning("Mislukt om pagina's op te halen: %s", url)
            return "", "Externe pagina"
        
        soup = BeautifulSoup(res.text, "html.parser")

        title_tag = soup.find("title")
        page_title = title_tag.get_text(strip=True) if title_tag else "Externe pagina"

        for tag in soup([
            "script", "style", "nav", "header", "footer",
            "aside", "form", "button"
        ]):
            tag.decompose()

        main = soup.find("main") or soup.find("article")

        if main:
            content_html = str(main)
        else:
            content_html = str(soup.body) if soup.body else str(soup)
        
        text = md(content_html)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return normalize_text(text), page_title
    
    except Exception as e:
        logger.warning("Fout bij scrapen %s: %s", url, e)
        return "", "Externe pagina"

def is_valid_external(url:str) -> bool:
    host = (urlparse(url).hostname or "").lower()

    bad_paths = [
    "download",
    "thanks",
    "chrome",
    "firefox",
    "signup",
    "login",
    "register"
    ]

    if any(p in url.lower() for p in bad_paths):
        return False

    if "sharepoint.com" in host:
        return False
    
    if "microsoftonline.com" in host:
        return False
    
    if "topdesk.net" in host:
        return False
    
    if "instructure.com" in host:
        return False

    if "canvaslms.com" in host:
        return False
    
    return True

# @register_loader("sharepoint_external_links", schema={
#     "site_id": {"type": "string", "required": True},
#     "label": {"type": "string", "required": False}
# })
# def load_sharepoint_external_links(config: dict):
#     site_id = config.get("site_id")
#     label = config.get("label", "Externe links loader")

#     seen_urls = set()

#     logger.info("Externe links loader gestart: %s", label)

#     pages =  get_cached_pages(site_id, label, fetch_all_sharepoint_pages)

#     logger.info("Aantal SharePoint pagina's gevonden: %s", len(pages))

#     for page in pages:
#         title = page["metadata"].get("title")
#         content = page["content"]

#         logger.info("Pagina: %s", title)

#         links = re.findall(r"\((https?://[^\s]+)\)", content)

#         filtered_links = [l for l in links if is_valid_external(l)]

#         logger.info("Aantal externe links gevonden: %s", len(filtered_links))

#         for link in filtered_links[:3]:
#             normalized = link.rstrip("/").lower()

#             if normalized in seen_urls:
#                 logger.info("Skip duplicate link: %s", link)
#                 continue

#             seen_urls.add(normalized)

#             logger.info("Scrapen van externe link: %s", link)

#             content, page_title = scrape_page(link)

#             if not content.strip():
#                 continue

#             metadata = {
#                 "source": "external",
#                 "source_type": "webpage",
#                 "url": link,
#                 "title": page_title,
#                 "parent_page": title
#             }

#             doc = Document(text=content, metadata=metadata)

#             doc.excluded_embed_metadata_keys = ["url"]
#             doc.excluded_llm_metadata_keys = ["url"]

#             yield doc