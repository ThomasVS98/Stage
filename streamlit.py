import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")

st.title("IT Assistent")

question = st.text_input("Stel een vraag")

if st.button("Vraag stellen"):
    if question:
        with st.spinner("Bezig met het beantwoorden van de vraag..."):
            response = requests.post(
                API_URL,
                json={"question": question}
            )

        data = response.json()
        st.subheader("Antwoord:")
        st.write(data["answer"])

        if data["sources"]:
            st.subheader("Bronnen:")
            for source in data["sources"]:
                st.write(f"- {source}")