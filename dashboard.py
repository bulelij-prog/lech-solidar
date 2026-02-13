import streamlit as st
import base64
import json
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "syndicat-novembre-2025"
LOCATION = "us-central1" 

# Liste mise à jour avec les noms techniques des modèles récents
MODELS_TO_TRY = [
    "gemini-1.5-pro-002",  # Version stable la plus récente
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro"
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

# Initialisation directe sans boucle de test (pour éviter les blocages de cache)
creds = get_creds()
if creds:
    vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=creds)

with st.sidebar:
    st.title("⚡ NExUS Status")
    if creds:
        st.success("✅ Authentification OK")
    else:
        st.error("❌ Erreur de secrets")

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
        # On essaie de générer en bouclant sur les modèles ici
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
            except Exception as e:
                continue
        
        if not success:
            st.error("Désolé, aucun modèle ne répond. Google bloque l'accès API pour ce projet.")
            st.warning("Vérifiez l'onglet 'Facturation' (Billing) dans votre console Google Cloud.")
