import json
import re
from llama_index.core.llms import ChatMessage
from utils.logging import get_logger

VALID_INTENTS = ["SUPPORT", "ALGEMEEN", "IRRELEVANT"]
logger = get_logger(__name__)

def extract_json(text:str):
    matches = re.findall(r"\{.*?\}", text, re.DOTALL)
    return matches[0] if matches else None

def is_valid_query(q: str) -> bool:
    return bool(re.search(r"[a-zA-Z]{3,}", q))

def detect_intent_prompt(query:str)->str:
    return f"""
     Je bent een IT-dienst assistent voor de medewerkers van de Thomas More hogeschool

    Classificeer de vraag in EXACT één categorie:
    - SUPPORT
    - ALGEMEEN
    - IRRELEVANT

    REGELS:
    - Geef je antwoord ALLEEN in JSON formaat.
    - GEEN uitleg.
    - GEEN extra tekst.
    - Gebruik exact dit formaat:

    {{"intent": "SUPPORT"}}

    Voorbeelden:
    {{"intent": "SUPPORT"}}
    {{"intent": "ALGEMEEN"}}
    {{"intent": "IRRELEVANT"}}

    SUPPORT:
    Als de gebruiker hulp nodig heeft met IT-systemen, software of diensten.
    Dit omvat:
    - problemen (iets werkt niet)
    - hulpvragen (hoe gebruik ik iets?)
    - aanvragen (toegang, tools, VPN, accounts, etc.)

    Voorbeelden:
    - "Hoe reset ik mijn wachtwoord?"
    - "Mijn laptop maakt geen verbinding met wifi"
    - "Hoe gebruik ik VPN?"
    - "Kan ik toegang krijgen tot VPN?"
    - "Welke tools kan ik gebruiken voor remote werken?"

    ALGEMEEN:
    Informatieve vragen die niet over IT-systemen of IT-diensten gaan.
    Bijvoorbeeld:
    - "Wat zijn de openingsuren van de bib?"
    - "Wanneer start het academiejaar?"

    IRRELEVANT:
    Alles wat GEEN IT-gerelateerde vraag is, inclusief:
    - small talk ("Hoe gaat het?", "Zullen we een spel spelen?")
    - meningen ("Wat vind je van het weer?")
    - algemene kennis ("Is het goed weer?")
    - beledigingen ("Ben je een idioot?")

    BELANGRIJKE REGELS:
    - IT-gerelateerd (tools, toegang, systemen) → SUPPORT
    - Weer, spelletjes, meningen → IRRELEVANT
    - Twijfelgeval → kies IRRELEVANT

    Vraag: {query}
    """

def answer_system_prompt() -> str:
    return """Je bent een IT-assistent voor de medewerkers van de Thomas More hogeschool.

        RICHTLIJNEN:
        1. Antwoord uitsluitend op basis van de onderstaande context.
        2. Gebruik enkel expliciete informatie uit de context. Verzin nooit zelf informatie als die niet in context staat.
        3. Als een specifiek detail (zoals een knopnaam of URL) niet in de tekst staat, verzin deze dan niet.
        4. Zeg alleen "ik heb niet genoeg informatie" wanneer er GEEN bruikbare informatie in de context staat om de vraag te beantwoorden.
        5. Gebruik GEEN verwijzingen naar documenten, titels of bronnen in je antwoord.
        6. Behoud tijdslimieten, aantallen, voorwaarden en volgorde precies zoals ze in de context staan.
        7. Schrijf een duidelijk en direct antwoord voor de gebruiker. Gebruik NOOIT formuleringen zoals "volgens de context", "in de tekst staat", "het document zegt" of gelijkaardige bronverwijzingen.
        8. Geef een volledig antwoord en neem alle relevante stappen, voorwaarden en uitzonderingen uit de context op. Laat geen relevante informatie weg en vermijd duplicatie.
        9. Gebruik een bullet list wanneer er meerdere stappen of voorwaarden zijn.
            - Elk punt moet op een nieuwe lijn staan
            - Laat een lege lijn tussen elk bullet point
            - Elk bullet point bevat exact één voorwaarde of regel
        """

def answer_user_prompt(context:str, query:str)->str:
    return f"""
    Context:
    {context}

    Vraag:
    {query}

    Antwoord: 
    """
def detect_intent(llm, query:str):
    if not is_valid_query(query):
        return "IRRELEVANT"
    
    prompt = detect_intent_prompt(query)
    response = llm.complete(prompt)
    raw = response.text.strip()
    logger.info("RAW INTENT: %s", raw)

    json_str = extract_json(raw)
    if json_str:
        try:
            data = json.loads(json_str)
            intent = data.get("intent","").upper()
            if intent in VALID_INTENTS:
                logger.info("Gedetecteerde intent: %s", intent)
                return intent
        except Exception as e:
            logger.exception("Error occurred while parsing JSON: %s", e)

    raw_upper = raw.upper().strip()
    if raw_upper in VALID_INTENTS:
        logger.info("Gedetecteerde intent via fallback: %s", raw_upper)
        return raw_upper
    
    logger.warning("Intent detection failed for output: %s", raw)
    return "ONBEKEND"

def generate_answer(llm, context, query):
    messages = [
        ChatMessage(role="system", content=answer_system_prompt()),
        ChatMessage(role="user", content=answer_user_prompt(context, query))
    ]

    response = llm.chat(messages)

    return response.message.content
