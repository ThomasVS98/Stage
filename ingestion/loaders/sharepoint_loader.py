import os
import requests
import re
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import html
import urllib.parse
from llama_index.core import SimpleDirectoryReader
from markdownify import markdownify as md

load_dotenv()

CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET")
TENANT_ID = os.getenv("SHAREPOINT_TENANT_ID")
LMS_SITE_ID = os.getenv("LMS_SITE_ID")
SERVICE_CATALOG_ID = os.getenv("SERVICE_CATALOG_ID")

def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+\n", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

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
    # for tag in soup.find_all(["p", "div", "li", "h1", "h2", "h3", "h4", "br"]):
    #     tag.append("\n")

    # text = soup.get_text()

    # text = html.unescape(text)

    # # teveel whitespace opruimen
    # text = re.sub(r"[ \t]+", " ", text)
    # text = re.sub(r"\n\s*\n+", "\n\n", text)

    # return text.strip(), related_links


def fetch_all_sharepoint_pages(site_id, site_label):
    print(f"Ophalen Sharepoint pagina's van site: {site_label}")

    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    token = requests.post(token_url, data=token_data).json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    #ophalen
    pages_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/pages"
    res_pages = requests.get(pages_url, headers=headers)

    final_data = []

    if res_pages.status_code == 200:
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
                # Voeg alles samen met een witregel voor leesbaarheid
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
            print(f"Ingehaald: {title}")

        return final_data
    
def fetch_sharepoint_files(site_id, site_label):
    print(f"Ophalen Sharepoint bestanden van site: {site_label}")

    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    token = requests.post(token_url, data=token_data).json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    final_files = []
    folders_to_process = ["root"]
    visited_folders = set()
    seen_files = set()

    while folders_to_process:
        current_folder = folders_to_process.pop(0)

        if current_folder in visited_folders:
            continue
        visited_folders.add(current_folder)

        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/{current_folder}/children"

        if current_folder == "root":
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root/children"
        else:
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/items/{current_folder}/children"

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
                    print(f"Bestand gevonden: {name}")
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
        print(f"Fout bij downloaden: {e}")
        return False

# if __name__ == "__main__":
    
#     print("\n" + "="*50)
#     bestanden = fetch_sharepoint_files(LMS_SITE_ID, "LMS Site Files")
    
#     if bestanden:
#         test_file = bestanden[0]
#         dl_url = test_file["metadata"]["download_url"]
#         bestandsnaam = test_file["metadata"]["filename"]
#         temp_path = os.path.join("temp_test", bestandsnaam)
        
#         print(f"\nProberen te downloaden: {bestandsnaam}...")
#         if download_sharepoint_file(dl_url, temp_path):
#             print("✅ Download geslaagd! Tekst extraheren...")
            
#             # Gebruik SimpleDirectoryReader om het bestand te lezen
#             reader = SimpleDirectoryReader(input_files=[temp_path])
#             documents = reader.load_data()
            
#             if documents:
#                 content = documents[0].text
#                 print("-" * 30)
#                 print(f"Gevonden tekst (eerste 500 karakters):\n")
#                 print(content[:500] + "...")
#                 print("-" * 30)
#                 print(f"Totaal aantal karakters in dit document: {len(content)}")
#             else:
#                 print("❌ Geen tekst gevonden in het document. Is het een scan?")
#         else:
#             print("❌ Download mislukt.")