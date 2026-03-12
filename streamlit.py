import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")

# Admin functies
with st.sidebar:
    st.title("⚙️ Beheer")
    st.info("Voeg nieuwe bestanden toe aan de 'data' map en klik hieronder om de database bij te werken.")
    
    if st.button("🔄 Database Indexeren"):
        with st.spinner("Bezig met indexeren van documenten... dit kan even duren."):
            try:
                # ingest endpoint
                res = requests.post(f"{API_BASE_URL}/ingest", timeout=300) 
                if res.status_code == 200:
                    st.success("✅ Database succesvol bijgewerkt!")
                    # wis  cache zodat nieuwe index geladen wordt
                    st.cache_resource.clear()
                else:
                    st.error(f"Fout: {res.json().get('detail', 'Onbekende fout')}")
            except Exception as e:
                st.error(f"Verbindingsfout: {str(e)}")


#Hoofscherm
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