"""
NExUS v2.5 - Plan B (Ultra-allégé)
Diagnostic: Interface Streamlit + Gemini sans Discovery Engine
Test minimaliste pour vérifier le déploiement
"""

import streamlit as st
import google.generativeai as genai

# PAGE CONFIG
st.set_page_config(
      page_title="NExUS v2.5 - Plan B",
      page_icon="⚖️",
      layout="wide"
)

# INIT GEMINI
@st.cache_resource
def init_gemini():
      try:
                api_key = st.secrets.get("GOOGLE_API_KEY")
                if not api_key:
                              st.error("❌ GOOGLE_API_KEY manquant dans Streamlit Secrets")
                              st.stop()
                          genai.configure(api_key=api_key)
                return True
except Exception as e:
        st.error(f"❌ Erreur Gemini: {str(e)}")
        return False

# CALL GEMINI
def call_gemini(prompt: str, model: str = "gemini-2.0-flash") -> str:
      try:
                gmodel = genai.GenerativeModel(model)
                resp = gmodel.generate_content(prompt)
                return resp.text if resp.text else "Pas de réponse"
except Exception as e:
        return f"❌ Erreur: {str(e)}"

# INIT
if not init_gemini():
      st.stop()

# ===== UI =====
st.title("⚖️ NExUS v2.5 - Plan B")
st.markdown("**Test diagnostic: Interface + Gemini (sans Discovery Engine)**")
st.markdown("🧪 Si vous voyez cette page, c'est que Streamlit fonctionne!")
st.divider()

# SIDEBAR
with st.sidebar:
      st.header("⚙️ Config")
      model = st.selectbox("Gemini:", ["gemini-2.0-flash", "gemini-1.5-pro"], index=0)
      st.info("✅ Streamlit init")
      st.info("✅ Gemini API configured")

# HISTORIQUE
if "messages" not in st.session_state:
      st.session_state.messages = []

# AFFICHER HISTORIQUE
for msg in st.session_state.messages:
      with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

  # CHAT INPUT
  st.divider()
st.subheader("💬 Chat simple (pas de RAG)")

user_input = st.chat_input("Posez une question à Gemini...")

if user_input:
      # Ajouter user
      st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
              st.markdown(user_input)

    # Appel Gemini
    with st.chat_message("assistant"):
              with st.spinner("⏳ Gemini répond..."):
                            response = call_gemini(user_input, model)

              st.markdown(response)

        # Sauvegarde
              st.session_state.messages.append({"role": "assistant", "content": response})

st.divider()
st.caption("NExUS v2.5 - Plan B | Streamlit + google-generativeai | Test diagnostic")
