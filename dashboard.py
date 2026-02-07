import streamlit as st

st.set_page_config(page_title="NExUS - LECH Solidar", page_icon="✊", layout="wide")

st.markdown("<style>h1 { color: #E2001A; } h2 { color: #E2001A; }</style>", unsafe_allow_html=True)

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

st.button("🔍 Interroger la Base Juridique")
st.button("🗑️ Effacer")

st.divider()
st.caption("© 2025 CGSP - Commission Paritaire 330 | Région Bruxelles-Capitale")
