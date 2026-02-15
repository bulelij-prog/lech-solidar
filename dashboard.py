"""
NExUS v2.5 - Dashboard Principal avec RAG intégré
Utilise Vertex AI Discovery Engine pour les protocoles CHU Brugmann
Hiérarchie des normes: Loi > CCT > Protocole
Temperature: 0.1 (rigueur maximale)
"""

import streamlit as st
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import discoveryengine_v1
from google.cloud.discoveryengine_v1.services.search_service import SearchServiceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
# CONFIGURATION
# ================================================================

st.set_page_config(
        page_title="NExUS v2.5 - RAG Dashboard",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
)

# Configuration Discovery Engine
PROJECT_ID = "syndicat-novembre-2025"
LOCATION = "global"
DATA_STORE_ID = "nexus-cgsp-pdf-global"
HOSPITAL_FILTER = "iris_brugmann"

# Hiérarchie des normes (ordre de priorité)
DOC_TYPE_HIERARCHY = {
        "Loi": 3,
        "CCT": 2,
        "Protocole": 1
}

# ================================================================
# INITIALISATION VERTEX AI
# ================================================================

@st.cache_resource
def initialize_vertex_ai():
        """Initialise Vertex AI avec Service Account"""
        try:
                    service_account_json = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
                    if not service_account_json:
                                    st.error("❌ Erreur: GCP_SERVICE_ACCOUNT_JSON non configuré")
                                    st.stop()

                    credentials_dict = json.loads(service_account_json)
                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_dict
                    )

        project_id = credentials_dict.get("project_id")
            if not project_id:
                            st.error("❌ Impossible de récupérer le project_id")
                            st.stop()

        vertexai.init(project=project_id, credentials=credentials)
        return project_id, credentials

except Exception as e:
        st.error(f"❌ Erreur Vertex AI: {str(e)}")
        st.stop()


@st.cache_resource
def initialize_discovery_engine():
        """Initialise le client Discovery Engine"""
    try:
                return SearchServiceClient()
except Exception as e:
        logger.error(f"Erreur Discovery Engine: {str(e)}")
        return None


# ================================================================
# MOTEUR RAG INTÉGRÉ
# ================================================================

def search_datastore(
        query: str,
        doc_type_filter: Optional[str] = None,
        max_results: int = 5
) -> Tuple[List[Dict], str]:
        """
            Recherche sémantique dans le Data Store avec hiérarchie des normes

                    Hiérarchie:
                        1. Loi (priorité 3)
                            2. CCT (priorité 2)
                                3. Protocole (priorité 1)

                                        Args:
                                                query: Question utilisateur
                                                        doc_type_filter: Filtre optionnel (Loi, CCT, Protocole)
                                                                max_results: Nombre max de documents

                                                                            Returns:
                                                                                    Tuple[List[Dict], str]: (documents triés, contexte formaté)
                                                                                        """
    try:
                client = initialize_discovery_engine()
                if not client:
                                return [], ""

                # Construction de la requête
                search_config = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}"

        filter_str = f'hospital_id = "{HOSPITAL_FILTER}"'
        if doc_type_filter:
                        filter_str += f' AND doc_type = "{doc_type_filter}"'

        request = discoveryengine_v1.SearchRequest(
                        serving_config=search_config,
                        query=query,
                        page_size=max_results,
                        filter=filter_str,
                        content_search_spec={
                                            "snippet_spec": {
                                                                    "max_snippet_length": 500,
                                                                    "reference_only": False,
                                            },
                                            "summary_spec": {
                                                                    "summary_result_count": 5,
                                                                    "use_semantic_chunks": True,
                                            },
                        },
        )

        response = client.search(request)

        # Extraction et tri selon la hiérarchie
        documents = []
        for result in response.results:
                        doc = result.document
                        struct_data = doc.struct_data if hasattr(doc, 'struct_data') else {}

            filename = struct_data.get('file_name', 'Sans titre')
            doc_type = struct_data.get('doc_type', 'Protocole')  # Protocole par défaut
            snippet = result.snippet.snippet_status if hasattr(result, 'snippet') else ""

            doc_entry = {
                                'filename': filename,
                                'doc_type': doc_type,
                                'url': doc.uri if hasattr(doc, 'uri') else "",
                                'snippet': snippet,
                                'relevance_score': result.relevance_score if hasattr(result, 'relevance_score') else 0.0,
                                'hierarchy_priority': DOC_TYPE_HIERARCHY.get(doc_type, 0)
            }
            documents.append(doc_entry)

        # TRI par hiérarchie (Loi > CCT > Protocole) puis pertinence
        documents.sort(
                        key=lambda x: (-x['hierarchy_priority'], -x['relevance_score'])
        )

        # Construction du contexte
        context = "## 📚 CONTEXTE - Documents CHU Brugmann\n\n---\n"
        for idx, doc in enumerate(documents, 1):
                        context += f"""
                        **{idx}. [{doc['doc_type'].upper()}] {doc['filename']}**
                        📊 Pertinence: {doc['relevance_score']:.1%}
                        📌 Contenu: {doc['snippet'][:300]}...
                        """
                    context += "---\n"

        logger.info(f"✓ Recherche: {len(documents)} docs trouvés (Loi={sum(1 for d in documents if d['doc_type']=='Loi')}, CCT={sum(1 for d in documents if d['doc_type']=='CCT')}, Protocole={sum(1 for d in documents if d['doc_type']=='Protocole')})")

        return documents, context

except Exception as e:
        logger.error(f"❌ Erreur recherche: {str(e)}")
        return [], ""


def call_gemini_with_rag(
        prompt: str,
        model_name: str,
        rag_context: str,
        documents: list
) -> str:
        """
            Appelle Gemini avec augmentation RAG
                Temperature: 0.1 pour rigueur maximale
                    """
    try:
                augmented_prompt = f"""{rag_context}

                ## 📋 QUESTION UTILISATEUR
                {prompt}

                ## 📌 INSTRUCTIONS STRICTES
                - ⚖️ RÈGLE DE FAVEUR: Interprète toujours en faveur du travailleur/délégué
                - Cite OBLIGATOIREMENT tes sources (doc numéro et type)
                - Réponds UNIQUEMENT basé sur les documents ci-dessus
                - Si l'information n'existe pas, dis-le clairement
                - Structure: Titres, listes, références explicites
                - Référence les documents avec [DOC-1], [DOC-2], etc.
                """

        model = GenerativeModel(model_name=model_name)
        response = model.generate_content(
                        augmented_prompt,
                        generation_config={
                                            "max_output_tokens": 2048,
                                            "temperature": 0.1,  # RIGUEUR MAXIMALE
                        }
        )

        return response.text if response.text else "Pas de réponse disponible"

except Exception as e:
        logger.error(f"Erreur Gemini: {str(e)}")
        return f"Erreur: {str(e)}"


# ================================================================
# INITIALISATION
# ================================================================

project_id, credentials = initialize_vertex_ai()
st.success(f"✓ Vertex AI initialisé - Projet: {project_id}")

# ================================================================
# INTERFACE PRINCIPALE
# ================================================================

st.title("⚖️ NExUS v2.5 - RAG Dashboard")
st.markdown("**Assistant IA Expert - Secteur Aide aux Personnes | CHU Brugmann**")
st.markdown("*Hiérarchie des normes: Loi > CCT > Protocole | Temperature: 0.1 (Rigueur)*")
st.divider()

# SIDEBAR - Configuration
with st.sidebar:
        st.header("⚙️ Configuration RAG")

    model_choice = st.selectbox(
                "Modèle Gemini:",
                ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
                index=0
    )

    st.divider()

    st.subheader("🔍 Filtres Recherche")

    doc_type = st.selectbox(
                "Type de document:",
                ["Tous", "Loi", "CCT", "Protocole"],
                index=0
    )
    doc_type_filter = None if doc_type == "Tous" else doc_type

    max_results = st.slider(
                "Nombre de documents:",
                min_value=1,
                max_value=10,
                value=5
    )

    st.divider()
    st.info(f"📊 Projet: `{project_id}`")
    st.info("🔒 Temperature: **0.1** (Rigueur maximale)")
    st.info("📋 Règle de faveur: Appliquée")

# ZONE PRINCIPALE
col1, col2 = st.columns([2, 1])

with col1:
        st.subheader("💬 Assistant RAG + Gemini")

    prompt = st.text_area(
                "Posez votre question juridique:",
                placeholder="Ex: Quels sont mes droits de formation professionnelle?",
                height=150,
                key="user_prompt"
    )

    if st.button("🔍 Rechercher & Analyser", use_container_width=True):
                if prompt.strip():
                                with st.spinner("⏳ Recherche dans les protocoles..."):
                                                    # ÉTAPE 1: Recherche RAG
                                                    documents, rag_context = search_datastore(
                                                                            query=prompt,
                                                                            doc_type_filter=doc_type_filter,
                                                                            max_results=max_results
                                                    )

                if documents:
                                        st.success(f"✓ {len(documents)} documents trouvés")

                    # Affiche la distribution par type
                                        doc_counts = {}
                                        for doc in documents:
                                                                    doc_counts[doc['doc_type']] = doc_counts.get(doc['doc_type'], 0) + 1

                                        type_str = " | ".join([f"{dtype}: {count}" for dtype, count in sorted(doc_counts.items(), key=lambda x: -DOC_TYPE_HIERARCHY.get(x[0], 0))])
                                        st.caption(f"Distribution: {type_str}")

                    with st.spinner("⏳ Gemini analyse (température: 0.1)..."):
                                                # ÉTAPE 2: Appel Gemini
                                                response = call_gemini_with_rag(
                                                                                prompt=prompt,
                                                                                model_name=model_choice,
                                                                                rag_context=rag_context,
                                                                                documents=documents
                                                )

                        st.success("✓ Analyse complète")
                        st.markdown("---")
                        st.write(response)

                        # AFFICHAGE DES SOURCES
                        st.markdown("---")
                        st.subheader("📚 Sources consultées")

                        for idx, doc in enumerate(documents, 1):
                                                        icon = "⚖️" if doc['doc_type'] == "Loi" else "📋" if doc['doc_type'] == "CCT" else "📄"
                                                        st.markdown(
                                                            f"{icon} **[DOC-{idx}] {doc['filename']}** "
                                                            f"({doc['doc_type']}) - Pertinence: {doc['relevance_score']:.0%}"
                                                        )

                        # Sauvegarde historique
                        if "chat_history" not in st.session_state:
                                                        st.session_state.chat_history = []

                        st.session_state.chat_history.append({
                                                        "prompt": prompt,
                                                        "response": response,
                                                        "sources": [f"[DOC-{i}] {d['filename']}" for i, d in enumerate(documents, 1)],
                                                        "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
else:
                    st.warning("⚠️ Aucun document trouvé pour cette recherche")
else:
            st.warning("⚠️ Veuillez entrer une question")

with col2:
        st.subheader("📈 Stats")
    st.metric("Modèle", model_choice.split("-")[1])
    st.metric("Temperature", "0.1")
    st.metric("Timestamp", datetime.now().strftime("%H:%M:%S"))
    st.metric("Max Docs", max_results)
    st.metric("Règle faveur", "✓ Active")

# HISTORIQUE
st.divider()
st.subheader("📝 Historique")

if "chat_history" in st.session_state and st.session_state.chat_history:
        for i, entry in enumerate(st.session_state.chat_history, 1):
                    with st.expander(f"Interaction {i}: {entry['prompt'][:50]}..."):
                                    st.write(f"**Q:** {entry['prompt']}")
                                    st.write(f"**R:** {entry['response']}")
                                    st.write(f"**Sources:** {', '.join(entry['sources'])}")
                                    st.caption(f"⏰ {entry['timestamp']}")
else:
    st.info("Aucune interaction pour le moment")

st.divider()
st.caption("NExUS v2.5 | RAG + Gemini 2.0 Flash | Hiérarchie des normes | Règle de faveur")
