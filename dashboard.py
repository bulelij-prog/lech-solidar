import streamlit as st
import requests
import json
from datetime import datetime

# ====== CONFIGURATION SECRETS (SANS INDENTATION) ======
CLOUD_FUNCTION_URL = st.secrets.get("CLOUD_FUNCTION_URL", "")
PROJECT_ID = st.secrets.get("PROJECT_ID", "")
DATA_STORE_ID = st.secrets.get("DATA_STORE_ID", "")

# ====== PAGE CONFIG & STYLING CGSP ======
st.set_page_config(page_title="NExUS – LECH Solidar", page_icon="✊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.cgsp-header {
    background: linear-gradient(135deg, #E2001A 0%, #c41507 100%);
        color: white;
            padding: 30px;
                border-radius: 10px;
                    margin: 0 0 20px 0;
                        text-align: center;
                        }
                        .cgsp-header h1 {
                            margin: 0;
                                font-size: 2.5em;
                                    font-weight: bold;
                                    }
                                    .cgsp-header p {
                                        margin: 5px 0 0 0;
                                            font-size: 1.1em;
                                                opacity: 0.9;
                                                }
                                                .compliance-vert {
                                                    background-color: #d4edda;
                                                        color: #155724;
                                                            padding: 12px;
                                                                border-radius: 5px;
                                                                    font-weight: bold;
                                                                    }
                                                                    .compliance-rouge {
                                                                        background-color: #f8d7da;
                                                                            color: #721c24;
                                                                                padding: 12px;
                                                                                    border-radius: 5px;
                                                                                        font-weight: bold;
                                                                                        }
                                                                                        .service-box {
                                                                                            background-color: #f7f3ff;
                                                                                                border-left: 4px solid #E2001A;
                                                                                                    padding: 12px;
                                                                                                        margin: 10px 0;
                                                                                                        }
                                                                                                        </style>
                                                                                                        """, unsafe_allow_html=True)

st.markdown('<div class="cgsp-header"><h1>✊ NExUS - LECH Solidar</h1><p>L\'Intelligence au service des Camarades</p></div>', unsafe_allow_html=True)

st.markdown('⚖️ **Cadre Juridique**: CP 330 | Région Bruxelles-Capitale')

# ====== SIDEBAR CONFIGURATION ======
with st.sidebar:
        st.markdown('### 📋 Filtres de Recherche Juridique')

    st.markdown('**Commission Paritaire**')
    TARGET_CP = st.selectbox(
                'Sélectionnez votre commission:',
                ['CP 330 (Santé Publique)', 'CP 331 (Enseignement)', 'CP 332 (Private Sector)'],
                label_visibility='collapsed'
    )

    st.markdown('**Service**')
    SERVICE = st.selectbox(
                'Service:',
                ['Soins Infirmiers', 'Technique', 'Logistique', 'Administration', 'Direction'],
                label_visibility='collapsed'
    )

    st.markdown('**Statut de l\'Agent**')
    STATUT = st.selectbox(
                'Statut:',
                ['Statutaire/Nommé', 'Contractuel', 'Stagiaire', 'Étudiant'],
                label_visibility='collapsed'
    )

    st.markdown('---')
    st.markdown('### ℹ️ À Propos')
    st.info('💪 LECH Solidar - Construit avec ❤️ pour la défense des droits au CHU Brugmann')

# ====== TAB CREATION ======
tab1, tab2 = st.tabs(['💬 Chat Juridique', '📱 Générateur de Mobilisation'])

with tab1:
        st.markdown('### 💬 Interrogez les Archives Juridiques')
        st.markdown('Posez vos questions sur les protocoles CHU Brugmann, CP 330 et droits des syndicats.')

    question = st.text_area(
                '✍️ Votre question:',
                placeholder='Ex: "Un stagiaire a-t-il droit à la prime de fin d\'année ?"',
                height=100
    )

    col1, col2 = st.columns([3, 1])
    with col1:
                pass
            with col2:
                        if st.button('🔍 Interroger les Archives', type='primary'):
                                        if question.strip():
                                                            with st.spinner('⏳ Recherche en cours...'):
                                                                                    try:
                                                                                                                payload = {
                                                                                                                                                'query': question,
                                                                                                                                                'user_profile': {
                                                                                                                                                                                    'commission_paritaire': TARGET_CP,
                                                                                                                                                                                    'service': SERVICE,
                                                                                                                                                                                    'statut': STATUT
                                                                                                                                                    }
                                                                                                                    }
                                                                                                                
                        headers = {'Content-Type': 'application/json'}
                                        response = requests.post(CLOUD_FUNCTION_URL, json=payload, headers=headers, timeout=30)

                        if response.status_code == 200:
                                                        data = response.json()

                            st.markdown('---')
                            st.markdown('### ✅ Réponse de NExUS')

                            if 'fulfillment' in data and 'messages' in data['fulfillment']:
                                                                for msg in data['fulfillment']['messages']:
                                                                                                        st.markdown(msg.get('text', ''))

                                                            if 'compliance_score' in data:
                                                                                                score = data['compliance_score']
                                                                                                if score >= 80:
                                                                                                                                        st.markdown('<div class="compliance-vert">✅ Réponse Conforme - Score: ' + str(score) + '%</div>', unsafe_allow_html=True)
                                                                else:
                                    st.markdown('<div class="compliance-rouge">⚠️ Réponse Non Conforme - Score: ' + str(score) + '%</div>', unsafe_allow_html=True)

                                                                                                if 'violation_detected' in data and data['violation_detected']:
                                                                                                                                    st.warning('⚠️ Violation détectée - Veuillez consulter un délégué')
else:
                            st.error(f'Erreur serveur: {response.status_code}')

except Exception as e:
                        st.error(f'Erreur de connexion: {str(e)}')
else:
                st.warning('Veuillez poser une question')

with tab2:
        st.markdown('### 📱 Générateur de Mobilisation')
    st.markdown('Créez des messages de mobilisation pour vos camarades.')

    theme = st.selectbox(
                'Thème:',
                ['Droits syndicaux', 'Sécurité et santé', 'Conditions de travail', 'Discrimination', 'Harcèlement']
    )

    action = st.text_area(
                'Action demandée:',
                placeholder='Ex: "Exiger le respect de l\'accord du 12 décembre"',
                height=80
    )

    if st.button('📝 Générer le Tract', type='primary'):
                if action.strip():
                                st.markdown('---')
            st.markdown(f'### 📢 Tract - {theme}')
            st.markdown(f'> **Camarades**, {action.lower()}\n\n**Solidarité ✊**')
else:
            st.warning('Veuillez décrire l\'action')

# ====== FOOTER ======
st.markdown('---')
st.markdown('Construit avec ❤️ pour la défense des droits au CHU Brugmann | © 2025 CGSP')
