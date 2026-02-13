import streamlit as st
import base64
import json
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel

# Configuration
PROJECT_ID = "syndicat-novembre-2025"
LOCATION = "europe-west1"
MODEL_ID = "gemini-1.5-flash-001"

st.set_page_config(page_title="NExUS v2.5", layout="wide")

def get_credentials():
    b64_string = st.secrets["GCP_CREDENTIALS_BASE64"]
    json_info = json.loads(base64.b64decode(b64_string))
    return service_account.Credentials.from_service_account_info(
        json_info, scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

# Sidebar de diagnostic
with st.sidebar:
    st.title("Diagnostic")
    try:
        creds = get_credentials()
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=creds)
        st.success(f"✅ Connecté à {MODEL_ID}")
    except Exception as e:
        st.error(f"❌ Erreur de connexion : {e}")

# Application principale
st.title("🤖 NExUS v2.5")
st.caption("Assistant Syndical - Secteur Aide aux Personnes")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Posez votre question syndicale...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            model = GenerativeModel(MODEL_ID)
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Détail de l'erreur : {e}")
