"""
NExUS v2.5 - Dashboard Principal
Utilise Vertex AI avec Service Account pour l'authentification Gemini
"""

import streamlit as st
import json
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
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# INITIALISATION VERTEX AI AVEC SERVICE ACCOUNT
# ============================================================

@st.cache_resource
def initialize_vertex_ai():
    """
    Initialise Vertex AI avec les credentials du Service Account
    stockées dans les secrets Streamlit.
    
    Returns:
        tuple: (project_id, credentials)
    """
    try:
        # Récupère le JSON du service account depuis les secrets
        service_account_json = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
        
        if not service_account_json:
            st.error("❌ Erreur: Le secret GCP_SERVICE_ACCOUNT_JSON n'est pas configuré")
            st.error("Ajoute-le dans Streamlit Secrets avec le contenu de ta clé JSON")
            st.stop()
        
        # Parse le JSON
        try:
            credentials_dict = json.loads(service_account_json)
        except json.JSONDecodeError:
            st.error("❌ Erreur: GCP_SERVICE_ACCOUNT_JSON n'est pas un JSON valide")
            st.stop()
        
        # Crée les credentials
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict
        )
        
        # Récupère le project ID
        project_id = credentials_dict.get("project_id")
        
        if not project_id:
            st.error("❌ Erreur: Impossible de récupérer le project_id")
            st.stop()
        
        # Initialise Vertex AI
        vertexai.init(project=project_id, credentials=credentials)
        
        return project_id, credentials
    
    except Exception as e:
        st.error(f"❌ Erreur d'initialisation Vertex AI: {str(e)}")
        st.stop()


# ============================================================
# FONCTIONS POUR APPELER GEMINI
# ============================================================

def call_gemini_api(prompt: str, model_name: str = "gemini-2.0-flash") -> str:
    """
    Appelle l'API Gemini via Vertex AI.
    
    Args:
        prompt (str): Le prompt à envoyer à Gemini
        model_name (str): Le modèle Gemini à utiliser
    
    Returns:
        str: La réponse du modèle ou None si erreur
    """
    try:
        model = GenerativeModel(model_name=model_name)
        
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.7,
            }
        )
        
        return response.text
    
    except Exception as e:
        return f"Erreur Gemini: {str(e)}"


# ============================================================
# INITIALISATION AU DÉMARRAGE
# ============================================================

# Initialise Vertex AI
project_id, credentials = initialize_vertex_ai()

# Message de confirmation
st.success(f"✓ Vertex AI initialisé avec le projet: {project_id}")


# ============================================================
# INTERFACE STREAMLIT
# ============================================================

st.title("🚀 NExUS v2.5 - Dashboard")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    model_choice = st.selectbox(
        "Choisir le modèle Gemini:",
        ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
    )
    
    temperature = st.slider(
        "Température (créativité):",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.1
    )
    
    st.divider()
    st.info(f"📊 Projet GCP: `{project_id}`")


# Section principale
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Testeur Gemini")
    
    prompt = st.text_area(
        "Entrez votre prompt:",
        placeholder="Posez une question ou donnez une tâche à Gemini...",
        height=150
    )
    
    if st.button("🔄 Envoyer à Gemini", use_container_width=True):
        if prompt.strip():
            with st.spinner("⏳ Gemini réfléchit..."):
                response = call_gemini_api(prompt, model_name=model_choice)
                
                if response and not response.startswith("Erreur"):
                    st.success("✓ Réponse reçue")
                    st.markdown("---")
                    st.write(response)
                else:
                    st.error(response)
        else:
            st.warning("⚠️ Veuillez entrer un prompt")

with col2:
    st.subheader("📈 Stats")
    
    st.metric(
        "Modèle Actif",
        model_choice.split("-")[1]
    )
    
    st.metric(
        "Température",
        temperature
    )
    
    st.metric(
        "Timestamp",
        datetime.now().strftime("%H:%M:%S")
    )


# Section historique (optionnel)
st.divider()
st.subheader("📝 Historique")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if st.session_state.chat_history:
    for i, entry in enumerate(st.session_state.chat_history):
        with st.expander(f"Interaction {i+1}: {entry['prompt'][:50]}..."):
            st.write(f"**Prompt:** {entry['prompt']}")
            st.write(f"**Réponse:** {entry['response']}")
            st.caption(f"🕐 {entry['timestamp']}")
else:
    st.info("Aucune interaction pour le moment")


# Footer
st.divider()
st.caption("NExUS v2.5 | Powered by Vertex AI + Streamlit")
