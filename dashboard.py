import streamlit as st
import requests

st.set_page_config(page_title="NExUS - LECH Solidar", page_icon="✊", layout="wide")
st.markdown("<style>.header{color:#E2001A;}.footer{text-align:center;}</style>", unsafe_allow_html=True)

url = st.secrets.get("CLOUD_FUNCTION_URL", "")
if "messages" not in st.session_state:
              st.session_state.messages = []

st.sidebar.title("Configuration du Profil")
cp = st.sidebar.selectbox("Commission Paritaire", ["CP 330 (Santé Publique)", "Autre"])
service = st.sidebar.selectbox("Service", ["Soins", "Technique", "Logistique", "Admin", "Direction"])
statut = st.sidebar.selectbox("Statut", ["Statutaire", "Contractuel", "Stagiaire", "Étudiant"])

st.title("✊ NExUS - LECH Solidar")
st.subheader("Intelligence Juridique pour le CHU Brugmann")

col1, col2, col3 = st.columns(3)
col1.metric("Commission", cp.split("(")[0].strip())
col2.metric("Service", service)
col3.metric("Statut", statut)

st.divider()

st.write("**Posez votre question juridique:**")
question = st.text_area("", placeholder="Ex: Comment réclamer une prime d'ancienneté?", height=80)

col_submit, col_clear = st.columns(2)
submit = col_submit.button("🔍 Interroger la Base Juridique")
if col_clear.button("🗑️ Effacer"):
              st.session_state.messages = []
              st.rerun()

if submit and question:
              payload = {"query": question, "cp": cp, "service": service, "statut": statut}
              with st.spinner("En cours..."):
                                try:
                                                      resp = requests.post(url, json=payload, timeout=30)
                                                      if resp.status_code == 200:
                                                                                result = resp.json()
                                                                                msg = result.get("fulfillmentMessages", [{}])[0].get("text", {}).get("text", [""])[0] if result.get("fulfillmentMessages") else "Pas de réponse"
                                                                                score = result.get("compliance_score", 0)
                                                                                sources = result.get("sources", [])

                st.session_state.messages.append({"user": question})
                st.session_state.messages.append({"assistant": msg, "score": score, "sources": sources})

                st.success("Réponse trouvée")
                st.write(msg)
                if sources:
                                              st.subheader("Sources")
                                              for s in sources:
                                                                                st.write(f"• {s}")
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

st.divider()
st.markdown("<p style='text-align:center;font-size:0.85em;'>Construit pour défendre les droits au CHU Brugmann | © 2025 CGSP CP 330</p>", unsafe_allow_html=True)
