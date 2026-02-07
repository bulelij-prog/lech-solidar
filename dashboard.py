import streamlit as st
import requests
import json
from datetime import datetime

# ====== CONFIGURATION SECRETS (SANS INDENTATION) ======
CLOUD_FUNCTION_URL = st.secrets.get("CLOUD_FUNCTION_URL", "")
PROJECT_ID = st.secrets.get("PROJECT_ID", "")
DATA_STORE_ID = st.secrets.get("DATA_STORE_ID", "")

# ====== PAGE CONFIG & STYLING CGSP ======
st.set_page_config(page_title="NExUS - LECH Solidar", page_icon="✊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.cgsp-header { 
    background: linear-gradient(135deg, #E2001A 0%, #c41815 100%); 
        color: white; 
            padding: 30px; 
                border-radius: 10px; 
                    margin: 0 0 20px 0;
                        text-align: center;
                        }
                        .cgsp-header h1 { margin: 0; font-size: 2.5em; font-weight: bold; }
                        .cgsp-header p { margin: 5px 0 0 0; font-size: 1.1em; opacity: 0.9; }
                        .compliance-vert { 
                            background-color: #d4edda; 
                                color: #155724; 
                                    padding: 12px; 
                                        border-radius: 5px; 
                                            font-weight: bold; 
                                                border-left: 4px solid #28a745;
                                                }
                                                .compliance-rouge { 
                                                    background-color: #f8d7da; 
                                                        color: #721c24; 
                                                            padding: 12px; 
                                                                border-radius: 5px; 
                                                                    font-weight: bold; 
                                                                        border-left: 4px solid #dc3545;
                                                                        }
                                                                        .legal-banner {
                                                                            background-color: #f8f9fa;
                                                                                border-left: 4px solid #E2001A;
                                                                                    padding: 12px;
                                                                                        margin: 15px 0;
                                                                                            border-radius: 5px;
                                                                                            }
                                                                                            .footer-cgsp {
                                                                                                text-align: center;
                                                                                                    margin-top: 30px;
                                                                                                        padding-top: 20px;
                                                                                                            border-top: 2px solid #E2001A;
                                                                                                                font-size: 0.9em;
                                                                                                                    color: #666;
                                                                                                                    }
                                                                                                                    </style>
                                                                                                                    <div class="cgsp-header">
                                                                                                                        <h1>✊ NExUS - LECH Solidar</h1>
                                                                                                                            <p>L'Intelligence au service des Camarades</p>
                                                                                                                            </div>
                                                                                                                            """, unsafe_allow_html=True)

# ====== BARRE LATERALE - PARAMETRES JURIDIQUES ======
st.sidebar.markdown("### ⚖️ Paramètres du Secteur")

# Sélecteur Commission Paritaire (CP)
TARGET_CP = st.sidebar.selectbox(
        "Commission Paritaire",
        options=["CP 330"],
        index=0,
        help="Commission Paritaire pour la Santé Publique"
)

# Sélecteur Service
SERVICES = {
        "🏥 Soins Infirmiers": "soins_infirmiers",
        "⚙️ Technique": "technique",
        "🏢 Administration": "administration",
        "📦 Logistique": "logistique",
        "👔 Direction": "direction"
}
SERVICE = st.sidebar.selectbox(
        "Service",
        options=list(SERVICES.keys()),
        help="Sélectionnez votre département"
)
SERVICE_CODE = SERVICES[SERVICE]

# Sélecteur Statut de l'Agent
STATUTS = {
        "📋 Statutaire/Nommé": "statutaire",
        "📝 Contractuel": "contractuel",
        "🎓 Stagiaire": "stagiaire",
        "👨‍🎓 Étudiant": "etudiant"
}
STATUT = st.sidebar.selectbox(
        "Statut de l'Agent",
        options=list(STATUTS.keys()),
        help="Votre statut d'emploi"
)
STATUT_CODE = STATUTS[STATUT]

# Affichage du contexte juridique
st.sidebar.markdown("---")
st.sidebar.markdown("""
**📌 Contexte Juridique Actif:**
- **CP**: CP 330 (Santé Publique)
- **Région**: Bruxelles-Capitale
- **Bases Légales**: 
  - Iriscare / Santé Bruxelles
    - Moniteur Belge
      - Circulaires régionales
      """)

# ====== BANNEAU JURIDIQUE ======
st.markdown(f"""
<div class="legal-banner">
    <strong>⚖️ Cadre Juridique: CP 330 | Région Bruxelles-Capitale</strong><br>
        <small>Vous consultez en tant que: <strong>{STATUT}</strong> au service <strong>{SERVICE}</strong></small>
        </div>
        """, unsafe_allow_html=True)

# ====== ONGLETS PRINCIPAUX ======
tab1, tab2 = st.tabs(["💬 Chat Juridique", "📱 Générateur de Mobilisation"])

# ====== TAB 1: CHAT JURIDIQUE ======
with tab1:
        st.markdown("### 💬 Posez votre question aux Protocoles du CHU Brugmann")

    question_input = st.text_area(
                "Votre question:",
                placeholder="Ex: Un stagiaire a-t-il droit à la prime de fin d'année ?",
                height=100,
                label_visibility="collapsed"
    )

    if st.button("🔍 Interroger les Archives", type="primary", use_container_width=True):
                if question_input.strip():
                                with st.spinner("⏳ Recherche en cours dans les protocoles..."):
                                                    try:
                                                                            payload = {
                                                                                                        "question": question_input,
                                                                                                        "cp": TARGET_CP,
                                                                                                        "service": SERVICE_CODE,
                                                                                                        "statut": STATUT_CODE,
                                                                                                        "timestamp": datetime.now().isoformat()
                                                                                }

                    response = requests.post(
                                                CLOUD_FUNCTION_URL,
                                                json=payload,
                                                timeout=30
                    )

                    if response.status_code == 200:
                                                result = response.json()

                        # Afficher la réponse
                                                st.markdown("### 📖 Réponse de LECH Solidar")
                                                st.markdown(result.get("response", "Pas de réponse disponible"))

                        # Indicateur de conformité
                                                compliance = result.get("compliance_score", 0)
                        if compliance >= 0.8:
                                                        st.markdown(
                                                                                            '<div class="compliance-vert">✅ CONFORME - Information extraite des protocoles CHU Brugmann</div>',
                                                                                            unsafe_allow_html=True
                                                        )
else:
                            st.markdown(
                                                                '<div class="compliance-rouge">⚠️ VÉRIFICATION RECOMMANDÉE - Consultez un délégué permanent</div>',
                                                                unsafe_allow_html=True
                            )

                        # Sources
                            if "sources" in result:
                                                            st.markdown("**📚 Sources citées:**")
                                                            for source in result["sources"]:
                                                                                                st.write(f"• {source}")

                                                        # Bouton WhatsApp Alert
                                                        if result.get("violation_detected"):
                                                                                        st.warning("🚨 Violation potentielle détectée!")
                                                                                        if st.button("📲 Générer Alerte WhatsApp"):
                                                                                                                            whatsapp_msg = result.get("whatsapp_alert", "")
                                                                                                                            st.code(whatsapp_msg, language="text")
                                                                                                                            st.success("Message préparé pour partage WhatsApp")
                                                            else:
                        st.error(f"❌ Erreur API: {response.status_code}")

except requests.exceptions.Timeout:
                    st.error("⏱️ Délai d'attente dépassé. Veuillez réessayer.")
except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
else:
            st.warning("📝 Veuillez poser une question")

# ====== TAB 2: GENERATEUR DE MOBILISATION ======
with tab2:
        st.markdown("### 📱 Générateur de Tracts WhatsApp")

    tract_theme = st.selectbox(
                "Thème du tract",
                ["Prime de fin d'année", "Stagiaires - Droits", "Heures supplémentaires", "Congés", "Sécurité au travail"]
    )

    tract_audience = st.selectbox(
                "Public cible",
                ["Tous les agents", "Stagiaires", "Contractuels", "Personnels technique"]
    )

    if st.button("✍️ Générer le Tract", use_container_width=True):
                tract_content = f"""
                🚨 **{tract_theme}** 🚨

                Camarades,

                Ce tract concerne: **{tract_audience}**

                Réclamez vos droits basés sur:
                ✅ CP 330 (Santé Publique)
                ✅ Protocoles CHU Brugmann
                ✅ Région Bruxelles-Capitale

                **ENSEMBLE, AUCUNE RETRAIT!**
                Contactez votre délégué CGSP

                #UnionFaitLaForce #Solidarité #CGSPBreugmann
                        """
        st.text_area("Contenu du tract", value=tract_content, height=300)
        st.download_button("📥 Télécharger", data=tract_content, file_name=f"tract_{tract_theme}.txt")

# ====== FOOTER CGSP ======
st.markdown("""
<div class="footer-cgsp">
    Construit avec ❤️ pour la défense des droits au CHU Brugmann<br>
        © 2025 CGSP • NExUS - LECH Solidar<br>
            <small>v2.0 - Déploiement complet finalisé ✅</small>
            </div>
            """, unsafe_allow_html=True)
