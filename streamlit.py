import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/ask"

st.title("IT Assistent")

question = st.text_input("Stel een vraag")

if st.button("Vraag stellen"):
    if question:
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