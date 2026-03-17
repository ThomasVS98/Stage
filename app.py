import os
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")

if "answer" not in st.session_state:
    st.session_state.answer = None
if "sources" not in st.session_state:
    st.session_state.sources = []

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
        st.session_state.answer = data["answer"]
        st.session_state.sources = data["sources"]

if st.session_state.answer:
        st.subheader("Antwoord:")
        st.write(st.session_state.answer)
        if st.session_state.sources:
            st.subheader("Bronnen:")
            for source in st.session_state.sources:
                st.write(f"- {source}")