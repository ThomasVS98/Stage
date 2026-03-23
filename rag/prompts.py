def detect_intent_prompt(query:str)->str:
    return f"""
     Je bent een IT-dienst assistent voor de medewerkers van de Thomas More hogeschool

    Classificeer de vraag van de gebruiker in een van de volgende categorieën:

    - SUPPORT: De gebruiker heeft een specifieke vraag over het gebruik van een systeem, software of dienst. Bijvoorbeeld: "Hoe reset ik mijn wachtwoord?" of "Hoe maak ik verbinding met het Wi-Fi netwerk van de school?"
    - ALGEMEEN: De gebruiker stelt een algemene vraag die niet direct gerelateerd is aan IT-support. Bijvoorbeeld: "Wat zijn de openingstijden van de bibliotheek?"
    - IRRELEVANT: De vraag is niet relevant voor de IT-assistent of bevat ongepaste inhoud. Bijvoorbeeld: "Vertel een grap" of "Wat is de betekenis van het leven?"

    Vraag: {query}

    Antwoord enkel met één van de categorieën: SUPPORT, ALGEMEEN, IRRELEVANT.
    """

def answer_prompt(context:str, query:str)->str:
    return f"""
    Je bent een IT-assistent voor de medewerkers van de Thomas More hogeschool.

    RICHTLIJNEN:
    1. Antwoord uitsluitend op basis van de onderstaande context.
    2. Gebruik enkel expliciete informatie; maak onder geen omstandigheden aannames of eigen interpretaties.
    3. Als een specifiek detail (zoals een knopnaam of URL) niet in de tekst staat, verzin deze dan niet.
    4. Zeg alleen "ik heb niet genoeg informatie" wanneer er GEEN bruikbare informatie in de context staat om de vraag praktisch te beantwoorden.
    5. Gebruik GEEN verwijzingen naar documenten, titels of bronnen in je antwoord.
    6. Noem tijdslimieten, aantallen, voorwaarden en volgorde precies zoals ze in de context staan. Geef procedures en deadlines letterlijk weer.
    7. Schrijf een direct antwoord voor de gebruiker. Gebruik NOOIT formuleringen zoals "volgens de context", "in de tekst staat", "het document zegt" of gelijkaardige bronverwijzingen.
    8. Geef NOOIT je eigen mening of interpretaties. Volg de informatie van de context.
    9. Geef een volledig antwoord: neem alle relevante stappen, opties, uitzonderingen en waarschuwingen uit de context op. Laat niets zomaar weg.
    10. Structureer je antwoord in korte bullets wanneer er meerdere stappen/voorwaarden zijn.
    11. Als de context wel bruikbare informatie bevat, geef dan meteen een concreet antwoord zonder disclaimers over ontbrekende details.
        De rest kan blijven.

    Context:
    {context}

    Vraag:
    {query}

    Antwoord: 
    """

def detect_intent(llm, query:str):
    prompt = detect_intent_prompt(query)
    response = llm.complete(prompt)
    text =  response.text.strip().upper()

    if "SUPPORT" in text:
        return "SUPPORT"
    elif "ALGEMEEN" in text:
        return "ALGEMEEN"
    elif "IRRELEVANT" in text:
        return "IRRELEVANT" 
    return "ONBEKEND"

def generate_answer(llm, context, query):
    prompt = answer_prompt(context, query)
    return llm.stream_complete(prompt)
