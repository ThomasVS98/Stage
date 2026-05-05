from urllib.parse import urlparse
import ipaddress
import re
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from ingestion.preprocessing.cleaning import normalize_text
from utils.logging import get_logger

logger = get_logger(__name__)


def scrape_page(url: str) -> tuple[str, str]:
    """
    Scrapet een externe webpagina en extraheert leesbare tekst en titel.

    De functie:
    - volgt redirects en valideert de uiteindelijke URL
    - verwijdert irrelevante HTML elementen (scripts, navigatie, formulieren, afbeeldingen, etc.)
    - zet HTML om naar Markdown
    - normaliseert de tekst voor verdere verwerking

    Args:
        url (str): De URL van de externe pagina

    Returns:
        tuple[str, str]: Tuple met de gescrapete tekst en de paginatitel.
        Bij fouten of onveilige URL's wordt lege content geretourneerd.
    """
    try:
        res = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept-Language": "en-US,en;q=0.9",
            },
            allow_redirects=True,
        )

        final_url = res.url

        if not is_valid_external(final_url):
            logger.warning(
                "Redirect naar onveilige URL geblokkeerd: %s -> %s", url, final_url
            )
            return "", "Externe pagina"

        if res.status_code != 200:
            logger.warning("Mislukt om pagina's op te halen: %s", url)
            return "", "Externe pagina"

        soup = BeautifulSoup(res.text, "html.parser")

        title_tag = soup.find("title")
        page_title = title_tag.get_text(strip=True) if title_tag else "Externe pagina"

        for tag in soup(
            ["script", "style", "nav", "header", "footer", "aside", "form", "button"]
        ):
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


def is_valid_external(url: str) -> bool:
    """
    Controleert of een externe URL veilig en relevant is om te scrapen.

    Filtert o.a.:
    - niet-HTTP(s) URL's
    - lokale of private IP-adressen
    - ongewenste paden (download, login, etc.)
    - interne of bekende niet-relevante domeinen zoals SharePoint

    Args:
        url (str): De te valideren URL.

    Returns:
        bool: True indien de URL geschikt is voor scraping, anders False.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    host = parsed.hostname
    if not host:
        return False

    host = host.lower()

    if host == "localhost":
        return False

    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        pass

    bad_paths = [
        "download",
        "thanks",
        "chrome",
        "firefox",
        "signup",
        "login",
        "register",
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
