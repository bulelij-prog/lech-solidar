"""
NExUS Smoke Test - RESCUE MODE
Diagnostic minimaliste: Chat Gemini + Secret detection
Objectif: Vérifier clé API et interface seulement
"""

import streamlit as st
import google.generativeai as genai

# PAGE CONFIG
st.set_page_config(
      page_title="NExUS SMOKE TEST",
      page_icon="🧪",
      layout="wide"
)

st.title("🧪 NExUS SMOKE TEST - RESCUE MODE")
st.markdown("**Diagnostic: Chat Gemini + Secret Verification**")

# ============= SIDEBAR - DIAGNOSTIC =============
with st.sidebar:
      st.header("🔧 DIAGNOSTIC PANEL")
      st.divider()

    # Check Secret
      st.subheader("1️⃣ Secret Status")
      api_key = st.secrets.get("GOOGLE_API_KEY", None)
      if api_key:
                st.success(f"✅ GOOGLE_API_KEY found ({len(api_key)} chars)")
                key_preview = api_key[:10] + "..." + api_key[-5:]
                st.caption(f"Key preview: `{key_preview}`")
else:
        st.error("❌ GOOGLE_API_KEY NOT FOUND in Streamlit Secrets!")
          st.stop()

    st.divider()

    # Test genai connection
    st.subheader("2️⃣ Gemini Connection Test")
    try:
              genai.configure(api_key=api_key)
              st.success("✅ genai.configure() successful")

        # Try list_models
              try:
                            models = genai.list_models()
                            model_count = len([m for m in models if "generateContent" in str(m)])
                            st.success(f"✅ genai.list_models() works ({model_count} models found)")

            # Show available models
                  with st.expander("📋 Available Models"):
                                    for model in models:
                                                          if "generateContent" in str(model):
                                                                                    st.caption(f"• {model.name}")
except Exception as e:
            st.warning(f"⚠️ genai.list_models() failed: {str(e)[:100]}")

except Exception as e:
        st.error(f"❌ Gemini Config Failed: {str(e)}")
        st.stop()

    st.divider()

    # Model selector
    st.subheader("3️⃣ Model Selection")
    model_choice = st.selectbox(
              "Choose Gemini model:",
              ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
              index=0
    )
    st.info(f"Selected: **{model_choice}**")

# ============= MAIN: SIMPLE CHAT =============
st.divider()
st.subheader("💬 Simple Chat Test")
st.caption("Just type a question and test if Gemini responds")

# Initialize session state
if "messages" not in st.session_state:
      st.session_state.messages = []

# Display message history
for message in st.session_state.messages:
      with st.chat_message(message["role"]):
                st.markdown(message["content"])

# Chat input
user_input = st.chat_input("Ask something to test Gemini...")

if user_input:
      # Add user message
      st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
              st.markdown(user_input)

    # Get Gemini response
    try:
              with st.chat_message("assistant"):
                            with st.spinner("Gemini is thinking..."):
                                              gmodel = genai.GenerativeModel(model_choice)
                                              response = gmodel.generate_content(user_input)

                if response.text:
                                      st.markdown(response.text)
                                      st.session_state.messages.append({
                                          "role": "assistant",
                                          "content": response.text
                                      })
else:
                    st.error("Gemini returned empty response")

except Exception as e:
        st.error(f"❌ Gemini Error: {str(e)}")

# ============= DEBUG FOOTER =============
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
      st.metric("Messages in history", len(st.session_state.messages))
with col2:
      st.metric("Streamlit version", st.__version__)
with col3:
      st.metric("Mode", "RESCUE SMOKE TEST")

st.caption("🔧 If all 3 diagnostic checks are green: Setup is OK. Problem is elsewhere.")
