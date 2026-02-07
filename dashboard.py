import streamlit as st
import requests

st.set_page_config(page_title="NExUS - LECH Solidar", page_icon="✊", layout="wide")
st.markdown("<style>h1{color:#E2001A;}</style>", unsafe_allow_html=True)

url = st.secrets.get("CLOUD_FUNCTION_URL", "")
if "messages" not in st.session_state:
   st.session_state.messages = []

st.sidebar.title("Configuration")
cp = st.sidebar.selectbox("Commission", ["CP 330 (Santé)", "Autre"], index=0)
svc = st.sidebar.selectbox("Service", ["Soins", "Technique", "Logistique", "Admin", "Direction"], index=0)
stat = st.sidebar.selectbox("Statut", ["Statutaire", "Contractuel", "Stagiaire", "Étudiant"], index=0)

st.title("✊ NExUS - LECH Solidar")
st.write("Intelligence Juridique pour le CHU Brugmann")

c1, c2, c3 = st.columns(3)
c1.metric("CP", cp.split("(")[0])
c2.metric("Service", svc)
c3.metric("Statut", stat)

st.divider()
q = st.text_area("Question juridique:", placeholder="Ex: prime d'ancienneté?", height=80)

b1, b2 = st.columns(2)
if b1.button("🔍 Interroger"):
   if q:
       payload = {"query": q, "cp": cp, "service": svc, "statut": stat}
       try:
            r = requests.post(url, json=payload, timeout=30)
            if r.status_code == 200:
                  result = r.json()
                  msg = result.get("fulfillmentMessages", [{}])[0].get("text", {}).get("text", [""])[0] if result.get("fulfillmentMessages") else "Pas de réponse"
                  score = result.get("compliance_score", 0)
                  src = result.get("sources", [])
                  st.session_state.messages.append({"user": q})
                  st.session_state.messages.append({"assistant": msg})
                  st.success("Réponse trouvée")
                  st.write(msg)
                  if src:
                         st.subheader("Sources")
                         for s in src:
                                 st.write(f"• {s}")
                               st.metric("Conformité", f"{score}%")
            else:
                  st.error(f"Erreur {r.status_code}")
       except Exception as e:
            st.error(f"Erreur: {e}")

     if b2.button("🗑️ Effacer"):
        st.session_state.messages = []
        st.rerun()

if st.session_state.messages:
   st.divider()
 st.subheader("Historique")
 for m in st.session_state.messages:
     if "user" in m:
          st.write(f"👤 {m['user']}")
else:
   st.write(f"✊ {m['assistant']}")

st.divider()
st.caption("© 2025 CGSP CP 330 - Bruxelles-Capitale")
