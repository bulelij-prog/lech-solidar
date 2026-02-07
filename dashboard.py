import streamlit as st
import requests

st.set_page_config(page_title="NExUS - LECH Solidar", page_icon="✊", layout="wide")
st.markdown("<style>h1 { color: #E2001A; } h2 { color: #E2001A; }</style>", unsafe_allow_html=True)

cloud_url = st.secrets.get("CLOUD_FUNCTION_URL", "")
project_id = st.secrets.get("PROJECT_ID", "")

st.title("✊ NExUS - LECH Solidar")
st.write("Intelligence Juridique pour le CHU Brugmann")

st.sidebar.markdown("## ⚙️ Configuration du Profil")

cp = st.sidebar.selectbox("Commission Paritaire", ["CP 330 (Santé Publique)", "Autre CP"])
service = st.sidebar.selectbox("Service", ["Soins Infirmiers", "Technique", "Logistique", "Administration", "Direction"])
statut = st.sidebar.selectbox("Statut de l'Agent", ["Statutaire/Nommé", "Contractuel", "Stagiaire", "Étudiant"])

st.sidebar.markdown("---")
st.sidebar.write("**Région**: Bruxelles-Capitale")

st.divider()

c1, c2, c3 = st.columns(3)
c1.metric("Commission", "CP 330")
c2.metric("Service", service)
c3.metric("Statut", statut)

st.divider()
st.write("### Posez votre question juridique:")

question = st.text_area("Votre question", placeholder="Exemple: Comment réclamer une prime d'ancienneté si l'employeur refuse?", height=100)

b1, b2 = st.columns(2)

if b1.button("🔍 Interroger la Base Juridique"):
   if question.strip():
       payload = {
            "query": question,
            "commission_paritaire": cp,
            "service": service,
            "statut": statut,
            "region": "Bruxelles-Capitale"
       }
       with st.spinner("Interrogation de la base juridique en cours..."):
            response = requests.post(cloud_url, json=payload, timeout=30)
            if response.status_code == 200:
                  data = response.json()
                  messages = data.get("fulfillmentMessages", [])
                  if messages:
                         reply = messages[0].get("text", {}).get("text", ["Pas de réponse"])[0]
                         st.info(reply)
            else:
                   st.warning("Pas de réponse reçue")
   else:
         st.error(f"Erreur: {response.status_code}")
else:
    st.warning("Veuillez poser une question")

if b2.button("🗑️ Effacer"):
   pass

st.divider()
st.caption("© 2025 CGSP - Commission Paritaire 330 | Région Bruxelles-Capitale")
