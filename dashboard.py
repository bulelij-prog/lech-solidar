"""
NExUS v2.5  dashboard.py
Authentification par Base64  anti-corruption TOML
"""

import streamlit as st
import base64
import json
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel

st.set_page_config(page_title="NExUS v2.5 - CGSP", page_icon="", layout="wide")

def get_credentials():
    b64_string = st.secrets["GCP_CREDENTIALS_BASE64"]
    json_bytes = base64.b64decode(b64_string)
    creds_dict = json.loads(json_bytes)
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    return credentials

with st.sidebar:
    st.title(" NExUS v2.5")
    st.caption("Dlgation CGSP ALR")
    st.divider()
    
    st.subheader("1 Secret Base64")
    if "GCP_CREDENTIALS_BASE64" in st.secrets:
        b64_val = st.secrets["GCP_CREDENTIALS_BASE64"]
        st.success(f" Trouv ({len(b64_val)} caractres)")
    else:
        st.error(" GCP_CREDENTIALS_BASE64 introuvable")
        st.stop()
    
    st.subheader("2 Dcodage Base64")
    try:
        json_bytes = base64.b64decode(b64_val)
        creds_dict = json.loads(json_bytes)
        st.success(" JSON dcod")
        st.caption(f"project_id: {creds_dict.get('project_id')}")
        st.caption(f"client_email: {creds_dict.get('client_email')}")
    except Exception as e:
        st.error(f" chec : {e}")
        st.stop()
    
    st.subheader("3 Credentials Google")
    try:
        credentials = get_credentials()
        st.success(f" OK : {credentials.service_account_email}")
    except Exception as e:
        st.error(f" chec : {type(e).__name__}")
        st.stop()
    
    st.subheader("4 Vertex AI")
    try:
        vertexai.init(project="syndicat-novembre-2025", location="europe-west1", credentials=credentials)
        st.success(" Vertex AI initialis")
    except Exception as e:
        st.error(f" chec : {type(e).__name__}")
        st.stop()
    
    st.subheader("5 Modle Gemini")
    try:
        test_model = GenerativeModel("gemini-1.0-pro")
        st.success(" Modle prt")
    except Exception as e:
        st.error(f" chec : {type(e).__name__}")
        st.stop()
    
    st.divider()
    st.success(" TOUS SYSTMES OK")

def query_nexus(prompt: str) -> str:
    try:
        creds = get_credentials()
        vertexai.init(project="syndicat-novembre-2025", location="europe-west1", credentials=creds)
        model = GenerativeModel(
            model_name="gemini-1.0-pro",
            system_instruction="Tu es NExUS, l'assistant IA de la dlgation CGSP ALR. Rponds en franais.",
            generation_config={"max_output_tokens": 4096, "temperature": 0.3, "top_p": 0.8, "top_k": 40}
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f" {type(e).__name__} : {e}"

st.title(" NExUS v2.5  Dlgation CGSP")
st.markdown("*Assistant IA  Secteur Aide aux Personnes*")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Posez votre question syndicale...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours..."):
            result = query_nexus(prompt)
            st.markdown(result)
    st.session_state.messages.append({"role": "assistant", "content": result})

st.divider()
st.caption("NExUS v2.5  CGSP ALR  Propuls par Google Gemini")
