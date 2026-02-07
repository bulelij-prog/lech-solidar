import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="NExUS - LECH Solidar", page_icon="✊", layout="wide")

st.markdown("<style>.header{color:#E2001A;font-size:2.5em;font-weight:800;}.btn{color:#E2001A;}.footer{text-align:center;margin-top:40px;border-top:2px solid #E2001A;}</style>", unsafe_allow_html=True)

CLOUD_FUNCTION_URL = st.secrets.get("CLOUD_FUNCTION_URL", "")
PROJECT_ID = st.secrets.get("PROJECT_ID", "")
DATA_STORE_ID = st.secrets.get("DATA_STORE_ID", "")

if "messages" not in st.session_state:
          st.session_state.messages = []

st.sidebar.title("Configuration du Profil")
cp = st.sidebar.selectbox("Commission Paritaire", ["CP 330 (Santé Publique)", "Autre"])
service = st.sidebar.selectbox("Service", ["Soins", "Technique", "Logistique", "Admin", "Direction"])
statut = st.sidebar.selectbox("Statut", ["Statutaire", "Contractuel", "Stagiaire", "Étudiant"])

col1, col2 = st.columns(2)
col1.title("✊ NExUS - LECH Solidar")
col2.info("Intelligence Juridique pour les Camarades")

tab1, tab2 = st.tabs(["Chat Juridique", "Ressources"])

with tab1:
          st.subheader("Posez votre question")
          c1, c2, c3 = st.columns(3)
          c1.info(f"Commission: {cp.split('(')[0]}")
          c2.info(f"Service: {service}")
          c3.info(f"Statut: {statut}")

    question = st.text_area("Votre question", height=80)

    col_b, col_c = st.columns(2)
    submit = col_b.button("Interroger la Base Juridique")
    if col_c.button("Effacer"):
                  st.session_state.messages = []
                  st.rerun()

    if submit and question:
                  payload = {
                                    "query": question,
                                    "cp": cp,
                                    "service": service,
                                    "statut": statut,
                                    "region": "Bruxelles-Capitale"
                  }
                  with st.spinner("En cours..."):
                                    try:
                                                          resp = requests.post(CLOUD_FUNCTION_URL, json=payload, timeout=30)
                                                          if resp.status_code == 200:
                                                                                    result = resp.json()
                                                                                    msg = result.get("fulfillmentMessages", [{}])[0].get("text", {}).get("text", [""])[0] if result.get("fulfillmentMessages") else "Pas de réponse"
                                                                                    score = result.get("compliance_score", 0)
                                                                                    sources = result.get("sources", [])

                    st.session_state.messages.append({"user": question})
                    st.session_state.messages.append({"assistant": msg, "score": score})

                    st.success("Réponse trouvée")
                    st.write(msg)

                    if sources:
                                                  st.subheader("Sources Juridiques")
                                                  for src in sources:
                                                                                    st.write(f"• {src}")

                                              st.metric("Conformité", f"{score}%")
else:
                    st.error(f"Erreur serveur ({resp.status_code})")
except Exception as e:
                st.error(f"Erreur: {e}")

    if st.session_state.messages:
                  st.divider()
        st.subheader("Historique")
        for msg in st.session_state.messages:
                          if "user" in msg:
                                                st.write(f"👤 {msg['user']}")
else:
                st.write(f"✊ {msg['assistant']}")

with tab2:
          st.info("Protocoles CHU Brugmann | Circulaires | Tracts CGSP")

st.divider()
st.markdown("<p style='text-align:center;font-size:0.9em;'>Construit pour la défense des droits au CHU Brugmann | © 2025 CGSP CP 330</p>", unsafe_allow_html=True)
