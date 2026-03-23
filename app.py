import os
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

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

# Admin functies
with st.sidebar:
    st.title("⚙️ Beheer")
    st.info("Klik hieronder om de SharePoint pagina's en bestanden opnieuw te synchroniseren.")
    
    if st.button("🔄 Database Synchroniseren"):
        with st.spinner("Bezig met ophalen van SharePoint data... dit kan enkele minuten duren."):
            try:
                res = requests.post(f"{API_BASE_URL}/ingest", timeout=600) 
                
                if res.status_code == 200:
                    status_msg = res.json().get('message', 'Database succesvol bijgewerkt!')
                    st.success(f"✅ {status_msg}")
                    st.cache_resource.clear()
                else:
                    error_detail = res.json().get('detail', 'Onbekende fout')
                    st.error(f"Fout: {error_detail}")
            except requests.exceptions.Timeout:
                st.warning("⚠️ De server is nog bezig met indexeren, maar de verbinding met de interface is verbroken. Wacht een paar minuten en stel dan je vraag.")
            except Exception as e:
                st.error(f"Verbindingsfout: {str(e)}")
    
#Hoofdscherm
st.title("IT Assistent")

with st.form("vraag_form"):
    question = st.text_input("Stel een vraag")
    submitted = st.form_submit_button("Vraag stellen")

if submitted:
    if question:
        with st.spinner("Bezig met het beantwoorden van de vraag..."):
            response = requests.post(
                f'{API_BASE_URL}/ask',
                json={"question": question}
            )
        data = response.json()
        if data.get("action") == "INTAKE":
            res = requests.post(f"{API_BASE_URL}/intake/start")
            intake_data = res.json()

            st.session_state.mode = "intake"
            st.session_state.intake_session_id = intake_data["session_id"]
            st.session_state.current_question = intake_data["question"]
            st.session_state.answer = None
            st.session_state.sources = []
        else:
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
                data = res.json()

                if data.get("done"):
                    st.success("Intake afgerond")
                    st.json(data["data"])

                    st.session_state.mode = "chat"
                    st.session_state.intake_session_id = None
                    st.session_state.current_question = None
                else:
                    st.session_state.current_question = data["question"]
                    st.rerun()
