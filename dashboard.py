import streamlit as st
import base64
import json
import google.generativeai as genai
import vertexai
from vertexai.generative_models import GenerativeModel

# --- CONFIGURATION ---
st.set_page_config(page_title="NExUS v2.5", layout="wide")

def get_config():
    """Décode les secrets pour obtenir les credentials et la clé API."""
    try:
        b64_string = st.secrets["GCP_CREDENTIALS_BASE64"]
        return json.loads(base64.b64decode(b64_string))
    except Exception as e:
        st.error(f"Erreur de configuration : {e}")
        return None

config = get_config()

# --- BARRE LATÉRALE (DIAGNOSTIC) ---
with st.sidebar:
    st.title("⚡ État du Système")
    if config and "google_api_key" in config:
        st.success("✅ Clé AI Studio détectée")
        # On configure l'API principale (Plan B - Plus robuste)
        genai.configure(api_key=config["google_api_key"])
    else:
        st.warning("⚠️ Utilisation du mode Vertex AI standard")

# --- INTERFACE PRINCIPALE ---
st.title("🤖 NExUS v2.5")
st.caption("Assistant Syndical - Secteur Aide aux Personnes")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- LOGIQUE DE CHAT ---
prompt = st.chat_input("Posez votre question syndicale...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = ""
        try:
            # TENTATIVE 1 : Google AI Studio (Plan B - Pas de limite GCP)
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            response_text = response.text
            st.markdown(response_text)
            st.info("💡 Répondu via Google AI Studio")
        except Exception as e:
            st.warning(f"Échec AI Studio, tentative via Vertex AI... ({e})")
            try:
                # TENTATIVE 2 : Vertex AI (Plan A)
                from google.oauth2 import service_account
                creds = service_account.Credentials.from_service_account_info(config)
                vertexai.init(project=config["project_id"], location="us-central1", credentials=creds)
                v_model = GenerativeModel("gemini-1.5-pro")
                v_response = v_model.generate_content(prompt)
                response_text = v_response.text
                st.markdown(response_text)
                st.info("💡 Répondu via Vertex AI")
            except Exception as e2:
                st.error(f"Erreur critique : {e2}")
                st.info("Vérifiez vos quotas ou la validité de votre clé API.")

        if response_text:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
