import streamlit as st
import base64
import json
import vertexai
from vertexai.generative_models import GenerativeModel

# CONFIGURATION
PROJECT_ID = "syndicat-novembre-2025"
REGIONS = ["us-central1", "europe-west4"] # Les deux régions les plus robustes

# LISTE INTELLIGENTE DES MODÈLES (du plus récent au plus stable)
MODELS_TO_TRY = [
    "gemini-3-pro-preview", # Ton accès spécial
    "gemini-1.5-pro",       # Le standard haute performance
    "gemini-1.5-flash",     # Le plus rapide
    "gemini-1.0-pro"        # Le dernier recours
]

st.set_page_config(page_title="NExUS v2.5 - Multi-Modèles", layout="wide")

def get_creds():
    try:
        b64 = st.secrets["GCP_CREDENTIALS_BASE64"]
        return json.loads(base64.b64decode(b64))
    except Exception as e:
        st.error(f"Erreur de lecture des secrets: {e}")
        return None

@st.cache_resource(show_spinner="Analyse des accès Google Cloud...")
def find_working_config():
    info = get_creds()
    if not info: return None
    
    from google.oauth2 import service_account
    creds = service_account.Credentials.from_service_account_info(info)
    
    for region in REGIONS:
        for model_name in MODELS_TO_TRY:
            try:
                vertexai.init(project=PROJECT_ID, location=region, credentials=creds)
                test_model = GenerativeModel(model_name)
                # Test de connexion réel
                test_model.generate_content("ping")
                return {"region": region, "model": model_name, "creds": creds}
            except:
                continue
    return None

# --- INTERFACE ---
config = find_working_config()

with st.sidebar:
    st.title("⚡ NExUS Diagnostic")
    if config:
        st.success(f"✅ Connecté via {config['region']}")
        st.info(f"Modèle actif : {config['model']}")
    else:
        st.error("❌ Aucun modèle accessible.")
        st.warning("Vérifiez que la facturation est active sur votre projet GCP.")

st.title("🤖 NExUS v2.5")
st.caption("Assistant Syndical CGSP - Intelligence Artificielle")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

prompt = st.chat_input("Posez votre question juridique ou syndicale...")

if prompt and config:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            vertexai.init(project=PROJECT_ID, location=config['region'], credentials=config['creds'])
            model = GenerativeModel(config['model'])
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Erreur lors de la génération : {e}")
