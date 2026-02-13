"""
NExUS v3.0 - Assistant IA Vertex AI
Délégation CGSP ALR
Authentification par Base64 sécurisée
"""

import streamlit as st
import base64
import json
import sys
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel

# Configuration Streamlit
st.set_page_config(
        page_title="NExUS v3.0 - CGSP",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
)

# ============================================================================
# AUTHENTIFICATION & DIAGNOSTIQUE
# ============================================================================

def load_credentials_from_base64():
        """Charge et valide les credentials depuis Base64"""
        try:
                    if "GCP_CREDENTIALS_BASE64" not in st.secrets:
                                    return None, "❌ Secret GCP_CREDENTIALS_BASE64 introuvable"

                    b64_string = st.secrets["GCP_CREDENTIALS_BASE64"]
                    json_bytes = base64.b64decode(b64_string)
                    creds_dict = json.loads(json_bytes)

        credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
            return credentials, "✅ Credentials chargés"

except Exception as e:
        return None, f"❌ Erreur décodage Base64: {str(e)}"

def init_vertex_ai(credentials):
        """Initialise Vertex AI"""
    try:
                vertexai.init(
                                project="syndicat-novembre-2025",
                                location="europe-west1",
                                credentials=credentials
                )
                return True, "✅ Vertex AI initialisé"
except Exception as e:
        return False, f"❌ Erreur Vertex AI: {str(e)}"

def test_gemini_model():
        """Teste le modèle Gemini 1.5 Flash"""
    try:
                model = GenerativeModel("gemini-1.5-flash-001")
                return True, "✅ Modèle Gemini 1.5 Flash disponible"
except Exception as e:
        return False, f"❌ Erreur modèle: {str(e)}"

def run_diagnostics():
        """Lance le diagnostic complet au démarrage"""
    diag_results = []

    # Test 1 : Credentials
    creds, msg_creds = load_credentials_from_base64()
    diag_results.append(("Secret Base64", msg_creds, creds is not None))

    if creds is None:
                return diag_results, None

    # Test 2 : Vertex AI
    success_va, msg_va = init_vertex_ai(creds)
    diag_results.append(("Vertex AI Init", msg_va, success_va))

    if not success_va:
                return diag_results, creds

    # Test 3 : Modèle Gemini
    success_model, msg_model = test_gemini_model()
    diag_results.append(("Modèle Gemini 1.5", msg_model, success_model))

    return diag_results, creds if success_model else None

# ============================================================================
# INTERFACE DIAGNOSTIQUE (SIDEBAR)
# ============================================================================

with st.sidebar:
        st.header("🔐 NExUS v3.0")
    st.caption("Assistant IA - Délégation CGSP ALR")
    st.divider()

    # Lance les diagnostics
    diag_results, credentials = run_diagnostics()

    st.subheader("📊 État du système")

    for test_name, message, success in diag_results:
                col1, col2 = st.columns([0.3, 0.7])
                with col1:
                                st.write("✅" if success else "❌")
                            with col2:
                    st.caption(test_name)
                                        st.caption(message)
        st.divider()

    # Affiche le statut global
    all_ok = all(result[2] for result in diag_results)
    if all_ok:
                st.success("🟢 TOUS SYSTÈMES OPÉRATIONNELS")
        system_ready = True
else:
        st.error("🔴 SYSTÈME EN ERREUR - Vérifier la configuration")
        system_ready = False

# ============================================================================
# FONCTION PRINCIPALE DE REQUÊTE
# ============================================================================

def query_nexus(prompt: str) -> str:
        """Envoie une requête au modèle Gemini"""

    if not system_ready or credentials is None:
                return "❌ Système non initialisé. Vérifiez la configuration dans le diagnostic."

    try:
                # Réinitialise Vertex AI (évite les problèmes de session)
                vertexai.init(
                                project="syndicat-novembre-2025",
                                location="europe-west1",
                                credentials=credentials
                )

        # Crée le modèle
        model = GenerativeModel(
                        model_name="gemini-1.5-flash-001",
                        system_instruction="""Tu es NExUS, l'assistant IA officiel de la délégation CGSP ALR.
                        - Réponds toujours en français
                        - Sois précis et professionnel
                        - Fournis des réponses structurées et faciles à comprendre
                        - Si tu ne sais pas, dis-le clairement"""
        )

        # Génère la réponse
        response = model.generate_content(
                        prompt,
                        generation_config={
                                            "max_output_tokens": 2048,
                                            "temperature": 0.7,
                                            "top_p": 0.9,
                                            "top_k": 40
                        }
        )

        return response.text

except Exception as e:
        return f"⚠️ Erreur lors du traitement: {type(e).__name__}: {str(e)}"

# ============================================================================
# INTERFACE PRINCIPALE
# ============================================================================

st.title("🤖 NExUS v3.0")
st.markdown("**Assistant IA Secteur Aide aux Personnes**")
st.markdown("Délégation CGSP ALR")
st.divider()

# Initialise l'historique de messages
if "messages" not in st.session_state:
        st.session_state.messages = []

# Affiche l'historique
for message in st.session_state.messages:
        with st.chat_message(message["role"]):
                    st.markdown(message["content"])

# Entrée utilisateur
if system_ready:
        prompt = st.chat_input("Posez votre question à NExUS...")

    if prompt:
                # Affiche le message utilisateur
                with st.chat_message("user"):
                                st.markdown(prompt)
                            st.session_state.messages.append({"role": "user", "content": prompt})

        # Traite la requête
        with st.chat_message("assistant"):
                        with st.spinner("⚙️ Traitement en cours..."):
                                            response = query_nexus(prompt)
                                            st.markdown(response)

                    st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.warning("⚠️ Le système n'est pas opérationnel. Vérifiez la configuration dans le volet de diagnostic.")

st.divider()
st.caption("NExUS v3.0 - Powered by Google Gemini 1.5 Flash on Vertex AI")
