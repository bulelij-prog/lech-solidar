import streamlit as st
import base64
import json
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "syndicat-novembre-2025"

# LISTE DES RÉGIONS À TESTER (Priorité à la stabilité)
REGIONS = ["us-central1", "europe-west4", "europe-west1"]
MODELS = ["gemini-1.5-flash-001", "gemini-1.5-flash", "gemini-pro"]

st.set_page_config(page_title="NExUS v2.5 - Multi-Région", layout="wide")

def get_creds():
    b64 = st.secrets["GCP_CREDENTIALS_BASE64"]
    return json.loads(base64.b64decode(b64))

# --- RECHERCHE AUTOMATIQUE DE RÉGION ---
@st.cache_resource(show_spinner="Recherche du meilleur serveur...")
def find_working_config():
    info = get_creds()
    from google.oauth2 import service_account
    creds = service_account.Credentials.from_service_account_info(info)
    
    for region in REGIONS:
        for model_name in MODELS:
            try:
                vertexai.init(project=PROJECT_ID, location=region, credentials=creds)
                test_model = GenerativeModel(model_name)
                # Test réel avec un mot unique
                test_model.generate_content("test")
                return {"region": region, "model": model_name}
            except:
                continue
    return None

# --- INTERFACE ---
with st.sidebar:
    st.title("⚡ Diagnostic")
    config = find_working_config()
    if config:
        st.success(f"Connecté : {config['model']}")
        st.info(f"Région : {config['region']}")
    else:
        st.error("Aucun serveur disponible. Vérifiez vos quotas GCP.")

st.title("🤖 NExUS v2.5")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

prompt = st.chat_input("Votre question...")
if prompt and config:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            # On ré-initialise avec la config qui a marché
            info = get_creds()
            from google.oauth2 import service_account
            creds = service_account.Credentials.from_service_account_info(info)
            vertexai.init(project=PROJECT_ID, location=config['region'], credentials=creds)
            
            model = GenerativeModel(config['model'])
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Erreur : {e}")
