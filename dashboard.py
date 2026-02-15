"""
NExUS v2.5 - Dashboard Principal
Version Finale : Authentification via Service Account (Base64) + Vertex AI
"""

import streamlit as st
import json
import base64
import pandas as pd
from datetime import datetime
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel

# ============================================================
# CONFIGURATION STREAMLIT
# ============================================================

st.set_page_config(
    page_title="NExUS v2.5 - Dashboard",
    page_icon="🚀",
    layout="wide"
)

# ============================================================
# INITIALISATION TECHNIQUE (MOTEUR VERTEX AI)
# ============================================================

@st.cache_resource
def initialize_vertex_ai():
    """Décode le Base64 et initialise la connexion Google Cloud"""
    try:
        # Récupération du secret en Base64 (Recommandé)
        b64_json = st.secrets.get("GCP_SERVICE_ACCOUNT_BASE64")
        
        if not b64_json:
            st.error("❌ Secret 'GCP_SERVICE_ACCOUNT_BASE64' introuvable dans Streamlit.")
            st.stop()
            
        # Décodage et chargement
        decoded_json = base64.b64decode(b64_json).decode("utf-8")
        credentials_dict = json.loads(decoded_json)
        
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        project_id = credentials_dict.get("project_id")
        
        # Initialisation du SDK Vertex AI
        vertexai.init(project=project_id, credentials=credentials)
        return project_id
        
    except Exception as e:
        st.error(f"❌ Erreur d'initialisation : {str(e)}")
        st.stop()

# Lancement immédiat de l'initialisation
project_id = initialize_vertex_ai()

# ============================================================
# LOGIQUE GEMINI
# ============================================================

def call_gemini(prompt, model_name="gemini-2.0-flash"):
    try:
        model = GenerativeModel(model_name=model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Erreur Gemini: {str(e)}"

# ============================================================
# INTERFACE UTILISATEUR
# ============================================================

st.title("🚀 NExUS v2.5 - Secteur Aide aux Personnes")
st.success(f"✓ Connecté au projet GCP : {project_id}")

with st.sidebar:
    st.header("Paramètres")
    model_choice = st.selectbox("Modèle", ["gemini-2.0-flash", "gemini-1.5-pro"])
    st.divider()
    st.info("Le système utilise désormais un Compte de Service sécurisé.")

# Zone de Chat simple
prompt = st.chat_input("Posez votre question juridique ou syndicale...")

if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours..."):
            answer = call_gemini(prompt, model_name=model_choice)
            st.write(answer)
