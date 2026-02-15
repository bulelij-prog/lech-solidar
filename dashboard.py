"""
NExUS v2.5 - Plan B (ULTRA-MINIMALISTE)
Interface Streamlit + Gemini API sans Discovery Engine
Version stable et autonome
"""

import streamlit as st
import google.generativeai as genai

# PAGE CONFIG
st.set_page_config(
          page_title="NExUS v2.5 - Plan B",
          page_icon="⚖️",
          layout="wide",
          initial_sidebar_state="expanded"
)

# TITLE & DESCRIPTION
st.title("⚖️ NExUS v2.5 - Plan B")
st.markdown("**Test diagnostic: Chat Gemini sans RAG**")
st.markdown("🧪 Interface minimaliste pour vérifier le déploiement")

# INIT GEMINI
@st.cache_resource
def init_gemini():
          """Initialize Gemini API with GOOGLE_API_KEY from Streamlit Secrets"""
          try:
                        api_key = st.secrets.get("GOOGLE_API_KEY")
                        if not api_key:
                                          st.error("❌ GOOGLE_API_KEY manquant dans Streamlit Secrets")
                                          st.stop()
                                      genai.configure(api_key=api_key)
                        return True
except Exception as e:
        st.error(f"❌ Erreur initialization Gemini: {str(e)}")
        return False

# CALL GEMINI
def call_gemini(prompt: str, model: str = "gemini-2.0-flash") -> str:
          """Send prompt to Gemini and get response"""
          try:
                        gmodel = genai.GenerativeModel(model)
                        resp = gmodel.generate_content(prompt)
                        return resp.text if resp.text else "Pas de reponse"
except Exception as e:
        return f"Erreur Gemini: {str(e)}"

# INIT AND VERIFY
if not init_gemini():
          st.stop()

# SIDEBAR CONTROLS
with st.sidebar:
          st.header("Configuration")
          st.success("✅ Gemini API initialized")
          st.success("✅ Streamlit running")
          model_choice = st.selectbox(
              "Select Gemini model:",
              ["gemini-2.0-flash", "gemini-1.5-pro"],
              index=0
          )

# INITIALIZE SESSION STATE
if "messages" not in st.session_state:
          st.session_state.messages = []

# DISPLAY CONVERSATION HISTORY
st.subheader("💬 Conversation")
st.divider()

for message in st.session_state.messages:
          with st.chat_message(message["role"]):
                        st.markdown(message["content"])

      # CHAT INPUT
      user_input = st.chat_input("Ask a question to Gemini...")

if user_input:
          # Add user message to history
          st.session_state.messages.append({
                        "role": "user",
                        "content": user_input
          })

    # Display user message
          with st.chat_message("user"):
                        st.markdown(user_input)

          # Get Gemini response
          with st.chat_message("assistant"):
                        with st.spinner("Gemini is thinking..."):
                                          response = call_gemini(user_input, model_choice)
                                      st.markdown(response)

          # Add assistant response to history
          st.session_state.messages.append({
              "role": "assistant",
              "content": response
          })

# FOOTER
st.divider()
st.caption("NExUS v2.5 - Plan B | Streamlit + google-generativeai")
