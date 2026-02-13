import streamlit as st
import base64
import json
import vertexai
from vertexai.generative_models import GenerativeModel

# CONFIGURATION
PROJECT_ID = "syndicat-novembre-2025"
LOCATION = "us-central1" 

# LISTE TECHNIQUE DES MODÈLES (incluant les versions preview)
MODELS_TO_TRY = [
    "gemini-1.5-pro-002",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-pro-experimental"  # Équivalent API pour Gemini 3 Preview
]

st.set_page_config(page_title="NExUS v2.5", layout="wide")

def get_creds():
    try:
        b64 = st.secrets["GCP_CREDENTIALS_BASE64"]
        info = json.loads(base64.b64decode(b64))
        from google.oauth2 import service_account
        return service_account.Credentials.from_service_account_info(info)
    except:
        return None

creds = get_creds()
if creds:
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=creds)

with st.sidebar:
    st.title("⚡ NExUS Status")
    if creds:
        st.success("✅ Authentification OK")
    else:
        st.error("❌ Secrets manquants")

st.title("🤖 NExUS v2.5")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

prompt = st.chat_input("Votre question...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        success = False
        for model_name in MODELS_TO_TRY:
            try:
                model = GenerativeModel(model_name)
                response = model.generate_content(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.info(f"Répondu par : {model_name}")
                success = True
                break
            except:
                continue
        
        if not success:
            st.error("Désolé, aucun modèle ne répond via l'API.")
            st.warning("Action finale requise : Allez dans la Console GCP > IAM > Quotas et vérifiez que 'Generate Content requests per minute' n'est pas à 0.")
