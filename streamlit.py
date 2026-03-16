import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")

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

question = st.text_input("Stel een vraag")

if st.button("Vraag stellen"):
    if question:
        with st.spinner("Bezig met het beantwoorden van de vraag..."):
            response = requests.post(
                f'{API_BASE_URL}/ask',
                json={"question": question}
            )

        data = response.json()
        st.subheader("Antwoord:")
        st.write(data["answer"])

        if data["sources"]:
            st.subheader("Bronnen:")
            for source in data["sources"]:
                st.write(f"- {source}")