"""
NExUS v2.5 — dashboard.py
Version Finale Corrigée (Google AI Studio)
"""

import streamlit as st
import google.generativeai as genai

# ==========================================
# CONFIGURATION DE LA PAGE
# ==========================================
st.set_page_config(
    page_title="NExUS v2.5 - CGSP",
    page_icon="⚖️",
    layout="wide"
)

# ==========================================
# INSTRUCTIONS SYSTÈME (Personnalité)
# ==========================================
SYSTEM_INSTRUCTION = """Tu es NExUS, l'assistant juridique expert de la délégation CGSP ALR.
Ton rôle est d'aider les délégués en analysant les conventions collectives et le droit du travail.

Règles :
1. Sois précis et cite tes sources.
2. Structure tes réponses avec des titres et des listes.
3. Si tu n'es pas sûr, dis-le clairement.
"""

# ==========================================
# BARRE LATÉRALE - DIAGNOSTIC
# ==========================================
with st.sidebar:
    st.title("🛡️ Contrôle NExUS")
    st.caption("Délégation CGSP ALR")
    st.divider()

    st.subheader("📊 Status du Système")
    
    # Vérification de la Clé dans les Secrets
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success(f"✅ Clé API détectée")
        
        try:
            # Configuration de l'API
            genai.configure(api_key=api_key)
            
            # Utilisation de gemini-1.5-flash pour éviter l'erreur 404
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=SYSTEM_INSTRUCTION
            )
            st.info("🤖 Modèle : Gemini 1.5 Flash")
            st.success("🟢 SYSTÈME OPÉRATIONNEL")
        except Exception as e:
            st.error(f"❌ Erreur config : {e}")
            st.stop()
    else:
        st.error("❌ GOOGLE_API_KEY manquante dans Streamlit Secrets")
        st.stop()

# ==========================================
# INTERFACE DE CHAT
# ==========================================
st.title("⚖️ NExUS v2.5")
st.markdown("### *Assistant IA Expert - Secteur Aide aux Personnes*")
st.divider()

# Initialisation de l'historique
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie
if prompt := st.chat_input("Posez votre question juridique ou syndicale..."):
    # Ajouter le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Génération de la réponse
    with st.chat_message("assistant"):
        with st.spinner("⚖️ Analyse en cours..."):
            try:
                # Appel sécurisé au modèle
                response = model.generate_content(prompt)
                
                if response.text:
                    st.markdown(response.text)
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response.text
                    })
                else:
                    st.warning("L'IA n'a pas pu générer de réponse. Vérifiez vos filtres de sécurité.")
                    
            except Exception as e:
                st.error(f"❌ Erreur lors de la génération : {str(e)}")

# Footer
st.divider()
st.caption("NExUS v2.5 | CGSP ALR | Propulsé par Google AI Studio")
