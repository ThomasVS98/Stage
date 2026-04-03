import os, time, requests, uuid, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
from ingestion.loader_registry import get_available_loaders, get_schema
from utils.logging import setup_logging, get_logger
from config.settings import settings
import ingestion.loaders.sharepoint_loader
import ingestion.loaders.topdesk_loader
import ingestion.loaders.onedrive_loader

setup_logging()
logger = get_logger(__name__)

API_BASE_URL = settings.API_BASE_URL

if "mode" not in st.session_state:
    st.session_state.mode = "chat"
if "intake_data" not in st.session_state:
    st.session_state.intake_data = {}
if "answer" not in st.session_state:
    st.session_state.answer = None
if "chat_sources" not in st.session_state:
    st.session_state.chat_sources = []
if "source_configs" not in st.session_state:
    st.session_state.source_configs = []
if "intake_session_id" not in st.session_state:
    st.session_state.intake_session_id = None
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "adding_source" not in st.session_state:
    st.session_state.adding_source = False

tab_chat, tab_admin = st.tabs(["💬 Chat", "⚙️ Admin"])

# Tab 1: Chat Interface
with tab_chat:
    st.title("IT Assistent")

    with st.form("vraag_form"):
        question = st.text_input("Stel een vraag")
        submitted = st.form_submit_button("Vraag stellen")

    if submitted and question:
        logger.info("Vraag ontvangen in Streamlit")
        with st.spinner("Bezig met het beantwoorden van de vraag..."):
            try:
                response = requests.post(f'{API_BASE_URL}/ask', json={"question": question})
                data = response.json()

                if data.get("action") == "INTAKE":
                    res = requests.post(f"{API_BASE_URL}/intake/start",json={"original_question": question})
                    intake_data = res.json()
                    st.session_state.mode = "intake"
                    st.session_state.intake_session_id = intake_data["session_id"]
                    st.session_state.current_question = intake_data["question"]
                    st.session_state.answer = None
                    st.session_state.chat_sources = []
                    logger.info("Intake flow gestart")
                else:
                    st.session_state.mode = "chat"
                    st.session_state.answer = data["answer"]
                    st.session_state.chat_sources = data["sources"]
            except Exception as e:
                st.error("Er is een fout opgetreden bij het stellen van de vraag.")
                logger.exception("Fout bij vraag stellen: %s", e)

    # Antwoord tonen
    if st.session_state.answer:
        st.subheader("Antwoord:")
        st.markdown(st.session_state.answer)
        if st.session_state.chat_sources:
            st.subheader("Bronnen:")
            for source in st.session_state.chat_sources:
                st.write(f"- {source}")

    # Intake logica
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
            intake_submitted = st.form_submit_button("Volgende")

        if intake_submitted:
            if not answer:
                st.warning("Gelieve een antwoord in te vullen.")
            else:
                res = requests.post(
                    f"{API_BASE_URL}/intake/answer",
                    json={"session_id": st.session_state.intake_session_id, "answer": answer}
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

                    elif data.get("done"):
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

# Tab 2: Admin functies
with tab_admin:
    def fetch_sources_to_state():
        """Haalt bronnen op van API en zet ze in de session state."""
        try:
            res = requests.get(f"{API_BASE_URL}/sources", timeout=10)
            res.raise_for_status()
            st.session_state.source_configs = res.json()
        except Exception as e:
            st.error(f"Fout bij ophalen bronnen: {e}")
            logger.exception("API Error bij ophalen bronnen: %s", e)

    if not st.session_state.source_configs:
        fetch_sources_to_state()

    def save_all_sources(source_list, action_name="Wijzigingen"):
        try:
            res = requests.post(f"{API_BASE_URL}/sources", json=source_list, timeout=10)
            if res.status_code == 200:
                st.session_state.source_configs = source_list
                st.toast(f"{action_name} succesvol doorgevoerd!", icon="💾")
                time.sleep(0.8)
                return True
            else:
                try:
                    error_data = res.json()
                    detail = error_data.get("detail", [])
                    if isinstance(detail, list) and len(detail) > 0:
                        err = detail[0]
                        loc = err.get("loc", [])
                        field = loc[-1] if loc else "onbekend"
                        msg = err.get("msg", "Ongeldig")
                        friendly_error = f"Veld '{field}' is verplicht of bevat een fout: {msg}"
                    else:
                        friendly_error = error_data.get("detail", res.text)
                except:
                    friendly_error = res.text

                st.error(f"Fout bij opslaan bronnen: {friendly_error}")
                return False
            
        except Exception as e:
            st.error(f"Verbindingsfout: {e}")
            logger.exception("Opslaan mislukt")
            return False

    # @st.cache_data
    # def get_sources():
    #     res = requests.get(f"{API_BASE_URL}/sources")
    #     return res.json()

    @st.cache_data
    def get_loader_types():
        return get_available_loaders()
    
    st.header("Admin Beheer")

    # Database synchronisatie
    st.subheader("Database Synchronisatie")
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

    # Bestaande bronnen aanpassen
    st.subheader("Bronnen configuratie")
    sources = st.session_state.source_configs

    for src in sources:
        if "id" not in src:
            src["id"] = str(uuid.uuid4())

    updated_sources = []
    for i, src in enumerate(sources):
        uid = src["id"]
        with st.expander(f"Bron {i+1}: {src.get('type','nieuw')}"):
            available_types = get_loader_types()

            if not available_types:
                st.warning("Geen loaders beschikbaar/gevonden")

            source_type = st.selectbox(
                "Type",
                options=available_types,
                index=available_types.index(src["type"]) if src["type"] in available_types else 0,
                key=f"type_{uid}"
            )

            type_key = f"type_state_{uid}"

            if type_key not in st.session_state:
                st.session_state[type_key] = source_type
                config = src.get("config", {})

            elif st.session_state[type_key] != source_type:
                st.session_state[type_key] = source_type

                config = {}

                for k in list(st.session_state.keys()):
                    if k.endswith(f"_{uid}") and not k.startswith("type_state"):
                        del st.session_state[k]
            else:
                config = src.get("config", {})

            enabled = st.checkbox(
                "Enabled",
                value=src.get("enabled",True),
                key=f"enabled_{uid}"
            )

            schema = get_schema(source_type)
            new_config = {}


            for field, rules in schema.items():
                field_type = rules.get("type")
                key = f"{field}_{uid}"

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
                "id": uid,
                "type": source_type,
                "enabled":enabled,
                "config": new_config
            })

            if st.button(f"❌ Verwijder bron {i+1}", key=f"delete_{uid}"):
                new_sources = [s for s in sources if s["id"] != uid]

                if save_all_sources(new_sources, action_name="Verwijdering"):
                    st.rerun()

            if st.button(f"💾 Opslaan bron {i+1}", key=f"save_{uid}"):
                new_sources = sources.copy()
                new_sources[i] = {
                    "id": uid,
                    "type": source_type,
                    "enabled": enabled,
                    "config": new_config
                }

                if save_all_sources(new_sources, action_name="Wijziging"):
                    st.rerun()


    st.divider()
    if st.button("➕ Nieuwe bron toevoegen"):
        st.session_state.adding_source = True

    if st.session_state.adding_source:
        st.subheader("Nieuwe bron toevoegen")

        available_types = get_loader_types()

        new_type = st.selectbox(
            "Type",
            options=available_types,
            key="new_type"
        )

        schema = get_schema(new_type)
        new_config = {}

        for field, rules in schema.items():
            field_type = rules.get("type")
            key = f"new_{field}"

            default = rules.get("default")
            if field_type == "bool":
                val = st.checkbox(
                    field,
                    value=bool(default),
                    key=key
                )
            elif field_type == "int":
                val = st.number_input(
                    field,
                    value=int(default or 0),
                    step=1,
                    format="%d",
                    key=key
                )
            else:
                val = st.text_input(
                    field,
                    value=str(default or ""),
                    key=key
                )
            new_config[field] = val

        enabled = st.checkbox("Enabled", value=True, key="new_enabled")
        if st.button("Toevoegen"):
            new_source = {
                "type": new_type,
                "enabled": enabled,
                "config": new_config
            }

            if save_all_sources(sources + [new_source], action_name="Toevoeging"):
                st.session_state.adding_source = False
                st.rerun()

        if st.button("Annuleren"):
            st.session_state.adding_source = False
            st.rerun()