"""
NExUS v2.5 — dashboard.py
Version stable : Google AI Studio
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
SYSTEM_INSTRUCTION = """Tu es NExUS, l'assistant juridique expert de la délégation CGSP ALR (secteur Aide aux Personnes).
Ton rôle est d'aider les délégués et les agents en analysant les conventions collectives, le droit du travail belge et les notes de service.

Règles de réponse :
1. Sois toujours précis et cite tes sources (articles de loi, numéros de CCT).
2. Utilise un ton professionnel, solidaire et pédagogique.
3. Si une information est manquante pour répondre avec certitude, demande des précisions.
4. Structure tes réponses avec des titres et des listes à puces pour la clarté.
"""

# ==========================================
# BARRE LATÉRALE - DIAGNOSTIC & STATUS
# ==========================================
with st.sidebar:
    st.title("🛡️ Contrôle NExUS")
    st.caption("Délégation CGSP ALR")
    st.divider()

    # Vérification de la Clé API
    st.subheader("📊 Status du Système")
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        # Affichage masqué pour sécurité
        st.success(f"✅ Clé API détectée ({api_key[:4]}...{api_key[-4:]})")
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                system_instruction=SYSTEM_INSTRUCTION
            )
            st.info("🤖 Modèle : Gemini 1.5 Pro")
            st.success("🟢 SYSTÈME OPÉRATIONNEL")
        except Exception as e:
            st.error(f"❌ Erreur config : {e}")
    else:
        st.error("❌ GOOGLE_API_KEY manquante dans les Secrets")
        st.stop()

    st.divider()
    st.markdown("### 💡 Aide rapide")
    st.info("Si l'IA ne répond pas, vérifiez vos quotas sur Google AI Studio.")

# ==========================================
# INTERFACE DE CHAT PRINCIPALE
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
        with st.spinner("⚖️ NExUS analyse la base juridique..."):
            try:
                # Appel à l'API Gemini
                response = model.generate_content(prompt)
                full_response = response.text
                
                st.markdown(full_response)
                
                # Sauvegarder la réponse
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response
                })
            except Exception as e:
                error_msg = f"Désolé, une erreur est survenue : {str(e)}"
                st.error(error_msg)

# Footer
st.divider()
st.caption("NExUS v2.5 | Outil interne CGSP ALR | Déployé via Google AI Studio")
