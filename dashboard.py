import streamlit as st
import os
import json
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel

def diagnostic_sidebar():
    st.sidebar.markdown("---")
    st.sidebar.markdown("##  MODE DIAGNOSTIC")
    st.sidebar.markdown("*Circuit GCP  Vertex AI  Gemini*")
    
    diag = {}
    
    st.sidebar.markdown("### 1 Secrets Streamlit")
    try:
        if hasattr(st, 'secrets') and st.secrets is not None:
            secret_keys = list(st.secrets.keys()) if hasattr(st.secrets, 'keys') else []
            if secret_keys:
                st.sidebar.success(" **Secrets trouvs**")
                st.sidebar.caption(f"Cls: {', '.join(secret_keys)}")
                diag['secrets'] = True
            else:
                st.sidebar.error(" **st.secrets vide**")
                diag['secrets'] = False
        else:
            st.sidebar.error(" **st.secrets indisponible**")
            diag['secrets'] = False
    except Exception as e:
        st.sidebar.error(" **Erreur lecture secrets**")
        st.sidebar.caption(f"Erreur: {str(e)[:80]}")
        diag['secrets'] = False
    
    st.sidebar.markdown("### 2 Bloc gcp_service_account")
    gcp_dict = None
    try:
        if "gcp_service_account" in st.secrets:
            gcp_raw = st.secrets["gcp_service_account"]
            if isinstance(gcp_raw, str):
                gcp_dict = json.loads(gcp_raw)
                st.sidebar.success(" **Bloc prsent (string)**")
            else:
                gcp_dict = gcp_raw
                st.sidebar.success(" **Bloc prsent (dict)**")
            
            required_keys = ['type', 'project_id', 'private_key', 'client_email']
            missing = [k for k in required_keys if k not in gcp_dict]
            
            if missing:
                st.sidebar.error(f" **Cls manquantes: {missing}**")
                diag['gcp_block'] = False
            else:
                st.sidebar.caption(f"Project: {gcp_dict.get('project_id', 'N/A')}")
                st.sidebar.caption(f"SA: {gcp_dict.get('client_email', 'N/A')[:50]}")
                diag['gcp_block'] = True
        else:
            st.sidebar.error(" **Bloc absent des secrets**")
            diag['gcp_block'] = False
    except json.JSONDecodeError as e:
        st.sidebar.error(" **JSON invalide**")
        st.sidebar.caption(f"Erreur parse: {str(e)[:80]}")
        diag['gcp_block'] = False
    except Exception as e:
        st.sidebar.error(" **Erreur bloc GCP**")
        st.sidebar.caption(f"Erreur: {str(e)[:80]}")
        diag['gcp_block'] = False
    
    st.sidebar.markdown("### 3 Credentials Google")
    gcp_credentials = None
    try:
        if gcp_dict:
            gcp_credentials = service_account.Credentials.from_service_account_info(
                gcp_dict,
                scopes=[
                    "https://www.googleapis.com/auth/cloud-platform",
                    "https://www.googleapis.com/auth/vertex-ai"
                ]
            )
            st.sidebar.success(" **Credentials crs**")
            st.sidebar.caption(f"Scopes: cloud-platform, vertex-ai")
            diag['credentials'] = True
        else:
            st.sidebar.error(" **Pas de bloc GCP**")
            diag['credentials'] = False
    except Exception as e:
        st.sidebar.error(" **Erreur cration credentials**")
        st.sidebar.caption(f"Erreur: {str(e)[:80]}")
        diag['credentials'] = False
    
    st.sidebar.markdown("### 4 Vertex AI")
    vertex_initialized = False
    try:
        if gcp_credentials and gcp_dict:
            vertexai.init(
                project=gcp_dict.get("project_id", "syndicat-novembre-2025"),
                location="europe-west1",
                credentials=gcp_credentials
            )
            st.sidebar.success(" **Vertex AI initialis**")
            st.sidebar.caption(f"Project: {gcp_dict.get('project_id', 'N/A')}")
            st.sidebar.caption(f"Location: europe-west1")
            diag['vertex'] = True
            vertex_initialized = True
        else:
            st.sidebar.error(" **Credentials non disponibles**")
            diag['vertex'] = False
    except Exception as e:
        st.sidebar.error(" **Erreur Vertex AI**")
        st.sidebar.caption(f"Erreur: {str(e)[:80]}")
        diag['vertex'] = False
    
    st.sidebar.markdown("### 5 Gemini 1.5 Pro")
    model_ready = False
    try:
        if vertex_initialized:
            model = GenerativeModel(model_name="gemini-1.5-pro")
            st.sidebar.success(" **Modle charg**")
            st.sidebar.caption(f"Modle: gemini-1.5-pro")
            st.sidebar.caption(f"Status: Prt ")
            diag['model'] = True
            model_ready = True
        else:
            st.sidebar.error(" **Vertex AI non initialis**")
            diag['model'] = False
    except Exception as e:
        st.sidebar.error(" **Erreur chargement modle**")
        st.sidebar.caption(f"Erreur: {str(e)[:80]}")
        diag['model'] = False
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("###  RSUM")
    
    passed = sum(1 for v in diag.values() if v)
    total = len(diag)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Tests russis", f"{passed}")
    with col2:
        st.metric("Total", f"{total}")
    
    if passed == total:
        st.sidebar.success(" **TOUS LES TESTS PASSENT!**")
        st.sidebar.info("L'application est prte  fonctionner.")
    elif passed >= 4:
        st.sidebar.warning(f" **{total - passed} test(s) chou(s)**")
    else:
        st.sidebar.error(f" **{total - passed} test(s) chou(s)**")
        st.sidebar.error("Vrifiez vos secrets dans Advanced Settings")
    
    st.sidebar.markdown("---")
    
    return diag, gcp_credentials, vertex_initialized, model_ready

st.set_page_config(
    page_title="NExUS v2.5 - CGSP",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton > button {
        background-color: #E63946;
        color: white;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        width: 100%;
        padding: 12px;
        font-size: 16px;
    }
    .stButton > button:hover {
        background-color: #c5242f;
        transform: scale(1.02);
    }
    h1 { color: #E63946; }
    h3 { color: #333; }
    </style>
""", unsafe_allow_html=True)

diag_results, gcp_creds, vertex_ok, model_ok = diagnostic_sidebar()

st.markdown("#  NExUS v2.5 - CGSP")
st.markdown("### Plateforme d'Intelligence Artificielle pour la CGSP")
st.markdown("*Assistant expert en relations sociales et droit du travail*")
st.markdown("---")

if not all(diag_results.values()):
    st.error(" Configuration incomplte")
    st.info("Consultez le **MODE DIAGNOSTIC** dans la barre latrale pour identifier le problme")
    st.stop()

col_input, col_info = st.columns([2, 1])

with col_input:
    st.markdown("###  Posez votre question ou analysez votre texte")
    
    user_input = st.text_area(
        "Entrez votre texte, document ou question...",
        height=180,
        placeholder="Exemples:\n- Analysez cette lettre de licenciement\n- Comment ragir face  une restructuration ?\n- Interprtez cette clause du contrat...",
        key="user_input"
    )

col_button, col_empty = st.columns([1, 4])
with col_button:
    analyze_button = st.button(" Analyser", use_container_width=True, type="primary")

SYSTEM_INSTRUCTION = """Tu es NExUS v2.5, l'Assistant d'Intelligence Artificielle expert de la CGSP.

Tu reprsentes l'expertise collective des dlgus syndicaux de la Confdration Gnrale des Syndicats Professionnels.

RLE ET EXPERTISE:
- Dlgu syndical expriment en relations sociales et ngociation
- Expert en droit du travail, conventions collectives et Code du Travail
- Conseiller stratgique pour la dfense des droits des salaris
- Analyste de documents contractuels et lgaux

PRINCIPES DE RPONSE:
1. Langage formel et professionnel - appropri aux discussions avec la direction
2. Structure claire - utilise des points numrots et sections distinctes
3. Argumentation solide - cite le Code du Travail et conventions collectives quand pertinent
4. Perspective quilibre - reconnais les contraintes patronales tout en dfendant les salaris
5. Solutions concrtes - propose des chemins d'action ralistes et dfendables
6. Rigueur juridique - bas sur des fondements lgaux solides

DOMAINES DE COMPTENCE:
 Analyse de lettres de licenciement et contrats
 Interprtation de dcisions managriales
 Droit  la grve, congs, maternit
 Rmunration et avantages sociaux
 Sant et scurit au travail
 Harclement et discrimination
 Restructurations et suppressions d'emplois
 Ngociation collective

STYLE DE RPONSE:
- Structur et lisible
- Clair et sans jargon inutile
- Tonalit respectueuse mais assertive
- Prt  recommander recours lgaux si ncessaire

Contexte: Tu assistes les dlgus de la CGSP pour prparer des runions, ngociations, ou litiges avec la direction."""

if analyze_button:
    if not user_input.strip():
        st.warning(" Veuillez entrer du texte ou une question avant de lancer l'analyse")
    else:
        st.markdown("---")
        
        with st.spinner(" NExUS analyse votre demande... (cela peut prendre quelques secondes)"):
            try:
                model = GenerativeModel(
                    model_name="gemini-1.5-pro",
                    system_instruction=SYSTEM_INSTRUCTION
                )
                
                response = model.generate_content(user_input)
                
                st.markdown("###  Rponse de NExUS")
                st.markdown(response.text)
                
                with st.expander(" Dtails techniques"):
                    col_d1, col_d2, col_d3 = st.columns(3)
                    with col_d1:
                        st.metric("Tokens (input)", len(user_input.split()))
                    with col_d2:
                        st.metric("Modle", "Gemini 1.5 Pro")
                    with col_d3:
                        st.metric("Rgion", "europe-west1")
                
                st.markdown("---")
                if st.button(" Nouvelle analyse"):
                    st.rerun()
                
            except Exception as e:
                st.error(f" Erreur lors de l'analyse: {str(e)}")
                st.warning("""
                **Dpannage:**
                1. Vrifiez le MODE DIAGNOSTIC dans la barre latrale
                2. Assurez-vous que tous les tests sont au vert 
                3. Vrifiez votre connexion internet
                4. Redmarrez l'application via le menu  > Reboot app
                """)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 11px; margin-top: 30px;'>
<p>NExUS v2.5  2026 CGSP | Powered by Gemini 1.5 Pro |  Authentification GCP Explicite</p>
<p style='font-size: 10px; color: #aaa;'>Assistant de dlgus syndicaux | Expertise en relations sociales et droit du travail</p>
</div>
""", unsafe_allow_html=True)
