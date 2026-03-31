import os
import requests
from dotenv import load_dotenv
import streamlit as st
from ingestion.loader_registry import get_available_loaders, get_schema
from utils.logging import setup_logging, get_logger
import ingestion.loaders.sharepoint_loader
import ingestion.loaders.topdesk_loader

load_dotenv()

setup_logging()
logger = get_logger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL")

if "mode" not in st.session_state:
    st.session_state.mode = "chat"
if "intake_data" not in st.session_state:
    st.session_state.intake_data = {}
if "answer" not in st.session_state:
    st.session_state.answer = None
if "sources" not in st.session_state:
    st.session_state.sources = []
if "intake_session_id" not in st.session_state:
    st.session_state.intake_session_id = None
if "current_question" not in st.session_state:
    st.session_state.current_question = None

@st.cache_data
def get_sources():
    res = requests.get(f"{API_BASE_URL}/sources")
    return res.json()

@st.cache_data
def get_loader_types():
    return get_available_loaders()

# Admin functies
with st.sidebar:
    st.title("⚙️ Admin Beheer")
    st.info("Klik hieronder om de kennisbronnen opnieuw te synchroniseren.")
    
    if st.button("🔄 Database Synchroniseren"):
        logger.info("Database synchronisatie gestart door gebruiker")
        with st.spinner("Bezig met ophalen van data... dit kan enkele minuten duren."):
            try:
                res = requests.post(f"{API_BASE_URL}/ingest", timeout=600) 
                
                if res.status_code == 200:
                    status_msg = res.json().get('message', 'Database succesvol bijgewerkt!')
                    st.success(f"✅ {status_msg}")
                    logger.info("Database synchronisatie succesvol afgerond")
                    st.cache_resource.clear()
                else:
                    error_detail = res.json().get('detail', 'Onbekende fout')
                    st.error(f"Fout: {error_detail}")
            except requests.exceptions.Timeout:
                st.warning("⚠️ De server is nog bezig met indexeren, maar de verbinding met de interface is verbroken. Wacht een paar minuten en stel dan je vraag.")
                logger.warning("Timeout tijdens database synchronisatie")
            except Exception as e:
                st.error(f"Verbindingsfout: {str(e)}")
                logger.exception("Verbindingsfout tijdens synchronisatie: %s", e)
    st.divider()
    st.subheader("Bronnen configuratie")
    try:
        sources = get_sources()
    except Exception as e:
        st.error("Fout bij laden van bronnen")
        logger.exception("Bronnen ophalen mislukt: %s", e)
        sources = []

    updated_sources = []
    for i, src in enumerate(sources):
        with st.expander(f"Bron {i+1}: {src.get('type','nieuw')}"):
            available_types = get_loader_types()

            if not available_types:
                st.warning("Geen loaders beschikbaar/gevonden")

            source_type = st.selectbox(
                "Type",
                options=available_types,
                index=available_types.index(src["type"]) if src["type"] in available_types else 0,
                key=f"type_{i}"
            )

            type_key = f"type_state_{i}"

            if type_key not in st.session_state:
                st.session_state[type_key] = source_type
                config = src.get("config", {})

            elif st.session_state[type_key] != source_type:
                st.session_state[type_key] = source_type

                config = {}

                for k in list(st.session_state.keys()):
                    if k.endswith(f"_{i}") and not k.startswith("type_state"):
                        del st.session_state[k]
            else:
                config = src.get("config", {})

            enabled = st.checkbox(
                "Enabled",
                value=src.get("enabled",True),
                key=f"enabled_{i}"
            )

            schema = get_schema(source_type)
            new_config = {}


            for field, rules in schema.items():
                field_type = rules.get("type")
                key = f"{field}_{i}"

                default = config.get(field)
                if default is None:
                    default = rules.get("default")

                if field_type == "bool":
                    default = bool(default) if default is not None else False
                
                elif field_type == "int":
                    try:
                        default = int(default)
                    except:
                        default = rules.get("default", 0)

                if key not in st.session_state:
                    st.session_state[key] = default

                if field_type == "bool":
                    st.checkbox(
                        field,
                        key=key
                    )
                elif field_type == "int":
                    st.number_input(
                        field,
                        key=key,
                        step = 1,
                        format = "%d"
                    )
                else:
                    st.text_input(
                        field,
                        key=key
                    )
                new_config[field] = st.session_state[key]


            updated_sources.append({
                "type": source_type,
                "enabled":enabled,
                "config": new_config
            })

            if st.button(f"❌ Verwijder bron {i+1}", key=f"delete_{i}"):
                new_sources = sources.copy()
                new_sources.pop(i)

                try:
                    requests.post(f"{API_BASE_URL}/sources", json=new_sources)
                    st.success("Bron verwijderd")
                    get_sources.clear()
                except Exception as e:
                    st.error("Fout bij verwijderen")
                    logger.exception("Delete mislukt: %s", e)
                
                st.rerun()

            if st.button(f"💾 Opslaan bron {i+1}", key=f"save_{i}"):
                latest_sources = get_sources()
                new_sources = latest_sources.copy()
                new_sources[i] = {
                    "type": source_type,
                    "enabled": enabled,
                    "config": new_config
                }

                st.write("DEBUG - new_config:", new_config)
                st.write("DEBUG - new_sources[i]:", new_sources[i])

                try:
                    res = requests.post(
                        f"{API_BASE_URL}/sources",
                        json=new_sources
                    )

                    if res.status_code == 200:
                        st.success("Bron opgeslagen")
                        get_sources.clear()
                    else:
                        st.error("Fout bij opslaan")
                except Exception as e:
                    st.error("Fout bij opslaan")
                    logger.exception("Opslaan mislukt: %s", e)

                st.rerun()


    st.divider()

    if st.button("➕ Nieuwe bron toevoegen"):
        new_sources = sources + [{
            "type": "",
            "enabled": True,
            "config": {}
        }]

        try:
            res = requests.post(
                f"{API_BASE_URL}/sources", 
                json=new_sources
            )
            if res.status_code == 200:
                st.success("Nieuwe bron toegevoegd")
                get_sources.clear()
        except Exception as e:
            st.error("Fout bij toevoegen")
            logger.exception("Bron toevoegen mislukt: %s", e)

        st.rerun()

#Hoofdscherm
st.title("IT Assistent")

with st.form("vraag_form"):
    question = st.text_input("Stel een vraag")
    submitted = st.form_submit_button("Vraag stellen")

if submitted:
    if question:
        logger.info("Vraag ontvangen in Streamlit")
        with st.spinner("Bezig met het beantwoorden van de vraag..."):
            response = requests.post(
                f'{API_BASE_URL}/ask',
                json={"question": question}
            )
        data = response.json()
        if data.get("action") == "INTAKE":
            res = requests.post(f"{API_BASE_URL}/intake/start",json={"original_question": question})
            intake_data = res.json()

            st.session_state.mode = "intake"
            st.session_state.intake_session_id = intake_data["session_id"]
            st.session_state.current_question = intake_data["question"]
            st.session_state.answer = None
            st.session_state.sources = []

            logger.info("Intake flow gestart")
        else:
            st.session_state.mode = "chat"
            st.session_state.answer = data["answer"]
            st.session_state.sources = data["sources"]

if st.session_state.answer:
        st.subheader("Antwoord:")
        st.write(st.session_state.answer)
        if st.session_state.sources:
            st.subheader("Bronnen:")
            for source in st.session_state.sources:
                st.write(f"- {source}")

if st.session_state.mode == "intake":
    st.subheader("Intakeprocedure")
    st.info(
        "Ik kan met deze informatie geen volledig antwoord geven. "
        "Daarom start ik een intakeprocedure zodat er een ticket kan worden aangemaakt. "
        "Dit ticket zal vervolgens door de ICTS-dienst worden bekeken en behandeld."
    )
    st.write(st.session_state.current_question)
    with st.form(key="intake_form"):
        answer = st.text_input("Jouw antwoord", key=f"intake_input_{st.session_state.current_question}")
        submitted = st.form_submit_button("Volgende")
    if submitted:
            if not answer:
                st.warning("Gelieve een antwoord in te vullen.")
            else:
                res = requests.post(
                    f"{API_BASE_URL}/intake/answer",
                    json={
                        "session_id": st.session_state.intake_session_id,
                        "answer": answer
                    }
                )
                if res.status_code != 200:
                    error = res.json().get("detail", "Onbekende fout")
                    st.error(error)
                    st.stop()
                else:
                    data = res.json()

                if data.get("error"):
                    st.error(data["error"])
                    st.session_state.mode = "chat"
                    st.session_state.intake_session_id = None
                    st.session_state.current_question = None
                    st.stop()

                if data.get("done"):
                    st.success("Intake afgerond")

                    st.markdown("### Samenvatting van je aanvraag")
                    st.write(f"**Probleem / aanvraag:** {data['data'].get('beschrijving')}")
                    st.write(f"**Context:** {data['data'].get('context')}")
                    st.write(f"**Doel:** {data['data'].get('doel')}")

                    if data.get("similar_ticket"):
                        st.warning("Er bestaat momenteel al minstens 1 ticket die mogelijk relevant is voor jouw aanvraag. De ICTS dienst zal dit verder bekijken.")
                    if data.get("ticket"):
                        st.success(
                                f"✅ Je ticket werd succesvol aangemaakt.\n\n"
                                f"**Ticketnummer:** {data['ticket']['number']}\n\n"
                                "De ICTS-dienst zal dit verder behandelen."
                            )
                        # st.json(data["data"])
                        logger.info("Intake afgerond, ticket aangemaakt: %s", data["ticket"]["number"])

                    st.session_state.mode = "chat"
                    st.session_state.intake_session_id = None
                    st.session_state.current_question = None
                else:
                    st.session_state.current_question = data["question"]
                    st.rerun()
