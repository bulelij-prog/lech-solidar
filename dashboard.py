import streamlit as st
import requests

CLOUD_FUNCTION_URL = st.secrets.get("CLOUD_FUNCTION_URL", "")

st.set_page_config(page_title="NExUS - LECH Solidar", page_icon="✊", layout="wide")

st.title("✊ NExUS - LECH Solidar")
st.markdown("L'Intelligence au service des Camarades")
st.markdown("⚖️ Cadre Juridique: CP 330 | Région Bruxelles-Capitale")

st.sidebar.markdown("### 📋 Filtres de Recherche")
TARGET_CP = st.sidebar.selectbox("Commission Paritaire:", ["CP 330", "CP 331", "CP 332"])
SERVICE = st.sidebar.selectbox("Service:", ["Soins Infirmiers", "Technique", "Logistique", "Administration", "Direction"])
STATUT = st.sidebar.selectbox("Statut:", ["Statutaire", "Contractuel", "Stagiaire", "Étudiant"])

st.markdown("---")
st.markdown("### 💬 Posez votre question")
question = st.text_area("Votre question:", placeholder='Ex: "Un stagiaire a-t-il droit à la prime?"')

if st.button("🔍 Interroger les Archives"):
        if question.strip():
                    st.write("Recherche en cours...")
                    try:
                                    payload = {"query": question, "user_profile": {"cp": TARGET_CP, "service": SERVICE, "statut": STATUT}}
                                    response = requests.post(CLOUD_FUNCTION_URL, json=payload, timeout=10)
                                    if response.status_code == 200:
                                                        data = response.json()
                                                        st.success("Réponse trouvée!")
                                                        if "fulfillment" in data:
                                                                                for msg in data.get("fulfillment", {}).get("messages", []):
                                                                                                            st.write(msg.get("text", ""))
                                                            else:
                st.error(f"Erreur: {response.status_code}")
                    except Exception as e:
                                    st.error(f"Erreur: {str(e)}")
        else:
                    st.warning("Veuillez poser une question")

    st.markdown("---")
st.markdown("Construit avec ❤️ pour la défense des droits | © 2025 CGSP")
