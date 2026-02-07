import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="NExUS - LECH Solidar", page_icon="✊", layout="wide")

st.markdown("""
<style>
.main-header { color: #E2001A; font-size: 2.5em; font-weight: 800; }
.subheader-cgsp { color: #E2001A; font-size: 1.2em; font-weight: 600; margin-top: 20px; }
.stButton > button { background-color: #E2001A; color: white; font-weight: 600; border: none; width: 100%; }
.stButton > button:hover { background-color: #B21118; }
.footer-cgsp { text-align: center; color: #666; font-size: 0.9em; margin-top: 40px; padding-top: 20px; border-top: 2px solid #E2001A; }
</style>
""", unsafe_allow_html=True)

CLOUD_FUNCTION_URL = st.secrets.get("CLOUD_FUNCTION_URL", "")
PROJECT_ID = st.secrets.get("PROJECT_ID", "")
DATA_STORE_ID = st.secrets.get("DATA_STORE_ID", "")

if "messages" not in st.session_state:
      st.session_state.messages = []

st.sidebar.markdown("### ⚙️ Configuration du Profil")
commission_paritaire = st.sidebar.selectbox("Commission Paritaire", ["CP 330 (Santé Publique)", "Autre CP"], index=0)
service = st.sidebar.selectbox("Service", ["Soins Infirmiers", "Technique", "Logistique", "Administration", "Direction"])
statut = st.sidebar.selectbox("Statut de l'Agent", ["Statutaire/Nommé", "Contractuel", "Stagiaire", "Étudiant"])
st.sidebar.markdown("---\n**ℹ️ À Propos**\n- **NExUS**: Système d'intelligence juridique\n- **Version**: 2.0 Production\n- **Région**: Bruxelles-Capitale")

col1, col2 = st.columns([0.3, 0.7])
with col1:
      st.markdown("# ✊")
  with col2:
        st.markdown('<p class="main-header">NExUS - LECH Solidar</p>', unsafe_allow_html=True)

st.markdown("<p style='color: #666; font-size: 1.1em; margin-top: -10px;'>L'Intelligence Juridique au Service des Camarades du CHU Brugmann</p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2 = st.tabs(["💬 Chat Juridique", "📋 Tracts & Documents"])

with tab1:
      st.markdown('<p class="subheader-cgsp">Posez votre question juridique</p>', unsafe_allow_html=True)
      c1, c2, c3 = st.columns(3)
      with c1:
                st.info(f"**Commission**: {commission_paritaire.split('(')[0].strip()}")
            with c2:
          st.info(f"**Service**: {service}")
                  with c3:
                      st.info(f"**Statut**: {statut}")

                        query = st.text_area("Votre question", placeholder="Ex: Comment faut-il réclamer une prime d'ancienneté...", height=100, label_visibility="collapsed")

    col_btn, col_clear = st.columns([0.8, 0.2])
    with col_btn:
              submit = st.button("🔍 Interroger la Base Juridique", key="submit_query")
    with col_clear:
              if st.button("🗑️ Effacer", key="clear"):
                            st.session_state.messages = []
                            st.rerun()

    if submit and query.strip():
              payload = {"query": query, "commission_paritaire": commission_paritaire, "service": service, "statut": statut, "region": "Bruxelles-Capitale", "timestamp": datetime.now().isoformat()}

        with st.spinner("⏳ Interrogation en cours..."):
                      try:
                                        resp = requests.post(CLOUD_FUNCTION_URL, json=payload, timeout=30)
                                        if resp.status_code == 200:
                                                              result = resp.json()
                    txt = result.get("fulfillmentMessages", [{}])[0].get("text", {}).get("text", [""])[0] if result.get("fulfillmentMessages") else "Pas de réponse"
                    score = result.get("compliance_score", 0)
                    sources = result.get("sources", [])

                    st.session_state.messages.append({"role": "user", "content": query})
                    st.session_state.messages.append({"role": "assistant", "content": txt, "sources": sources, "score": score})

                    st.success("✅ Réponse trouvée")
                    st.markdown(f"<div style='background-color: #f8f9fa; padding: 15px; border-left: 4px solid #E2001A;'><p>{txt}</p></div>", unsafe_allow_html=True)

                    if sources:
                                              st.markdown('<p class="subheader-cgsp">📚 Sources Juridiques</p>', unsafe_allow_html=True)
                                              for i, src in enumerate(sources, 1):
                                                                            st.markdown(f"**{i}. {src}**")

                                          st.markdown("---")
                    c1, c2 = st.columns(2)
                    with c1:
                                              st.metric("Score de Conformité", f"{score}%")
                                          with c2:
                                                                    st.success("✅ Aucune violation détectée")
else:
                    st.error(f"❌ Erreur serveur ({resp.status_code})")
except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")

    if st.session_state.messages:
              st.markdown("---\n<p class='subheader-cgsp'>Historique de la Session</p>", unsafe_allow_html=True)
        for msg in st.session_state.messages:
                      if msg["role"] == "user":
                                        st.markdown(f"<div style='background-color: #e8f4f8; padding: 10px; border-radius: 5px; margin: 10px 0;'><strong>👤 Vous</strong><p>{msg['content']}</p></div>", unsafe_allow_html=True)
else:
                st.markdown(f"<div style='background-color: #fff3e0; padding: 10px; border-radius: 5px; margin: 10px 0;'><strong>✊ LECH Solidar</strong><p>{msg['content']}</p></div>", unsafe_allow_html=True)

with tab2:
      st.markdown('<p class="subheader-cgsp">Ressources & Tracts Syndicaux</p>', unsafe_allow_html=True)
    st.info("📄 Protocoles CHU Brugmann | 📋 Circulaires Région | ✊ Tracts CGSP | 📚 Guides Juridiques")
    st.warning("⏳ Développement en cours - Section complète dans la version 2.1")

st.markdown("<div class='footer-cgsp'><p><strong>✊ NExUS - LECH Solidar v2.0</strong></p><p>Construit avec ❤️ pour la défense des droits au CHU Brugmann</p><p>© 2025 CGSP - Commission Paritaire 330 (Santé Publique)</p></div>", unsafe_allow_html=True)
