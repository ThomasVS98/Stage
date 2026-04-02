import json
import re
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

def answer_prompt(context:str, query:str)->str:
    return f"""
    Je bent een IT-assistent voor de medewerkers van de Thomas More hogeschool.

    RICHTLIJNEN:
    1. Antwoord uitsluitend op basis van de onderstaande context.
    2. Gebruik enkel expliciete informatie uit de context.
       Voeg niets toe en laat niets weg.
       Je mag de informatie NIET samenvatten, herinterpreteren of vereenvoudigen.
    3. Als een specifiek detail (zoals een knopnaam of URL) niet in de tekst staat, verzin deze dan niet.
    4. Zeg alleen "ik heb niet genoeg informatie" wanneer er GEEN bruikbare informatie in de context staat om de vraag praktisch te beantwoorden.
    5. Gebruik GEEN verwijzingen naar documenten, titels of bronnen in je antwoord.
    6. Noem tijdslimieten, aantallen, voorwaarden en volgorde precies zoals ze in de context staan. Geef procedures en deadlines letterlijk weer.
    7. Schrijf een direct antwoord voor de gebruiker. Gebruik NOOIT formuleringen zoals "volgens de context", "in de tekst staat", "het document zegt" of gelijkaardige bronverwijzingen.
    8. Geef NOOIT je eigen mening of interpretaties. Volg de informatie van de context.
    9. Geef een volledig antwoord: neem alle stappen, voorwaarden, uitzonderingen en waarschuwingen uit de context op.
       Je mag GEEN enkel element weglaten, ook niet als het gelijkaardig lijkt aan andere elementen.
    10. Gebruik een bullet list wanneer er meerdere stappen of voorwaarden zijn.
        - Elk punt moet op een nieuwe lijn staan
        - Laat een lege lijn tussen elk bullet point
        - Elk bullet point bevat exact één voorwaarde of regel
    11. Behoud alle tijdsvoorwaarden exact zoals in de context. Als er meerdere periodes of datums zijn, moet je elke periode expliciet vermelden.
    12. Als twee regels op elkaar lijken, moet je ze toch apart vermelden. Je mag geen regels combineren tot één algemene regel.
    13. Gebruik geen compacte of inline opsommingen. Schrijf elke bullet volledig uit op een aparte lijn.


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
    prompt = answer_prompt(context, query)
    return llm.stream_complete(prompt)
