"""
NExUS v2.5 - Dashboard RAG avec Vertex AI Discovery Engine
Région EU - Hiérarchie des normes belges - Règle de faveur
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

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
# CONFIGURATION - RÉGION EU
# ================================================================

st.set_page_config(
            page_title="NExUS v2.5 - Protocoles CHU Brugmann",
            page_icon="⚖️",
            layout="wide",
            initial_sidebar_state="expanded"
)

# Configuration Discovery Engine - RÉGION EUROPE
PROJECT_ID = "syndicat-novembre-2025"
LOCATION = "eu"  # 🇪🇺 RÉGION EUROPE
DATA_STORE_ID = "nexus-cgsp-pdf-global"
HOSPITAL_FILTER = "iris_brugmann"

# Hiérarchie des normes belges
DOC_TYPE_HIERARCHY = {
            "Loi": 3,
            "CCT": 2,
            "Protocole": 1
}

# Prompt système - Règle de faveur
SYSTEM_PROMPT = """Tu es NExUS, assistant juridique expert pour les délégués syndicaux du CHU Brugmann.

🔴 RÈGLES ABSOLUES (application stricte):
1. ⚖️ RÈGLE DE FAVEUR: En cas de doute, interprète TOUJOURS en faveur du travailleur/délégué
2. 🇧🇪 HIÉRARCHIE BELGE: Loi > CCT > Protocole (applique cet ordre d'interprétation)
3. 📋 SOURCES: Cite obligatoirement [DOC-1], [DOC-2] etc. 
4. ❌ PAS D'INVENTION: Réponds UNIQUEMENT basé sur les documents fournis
5. 💯 PRÉCISION: Zéro hallucination, rigueur maximale

Si l'information n'est pas dans les documents, dis-le clairement.
Structure ta réponse avec titres, listes à puces, références explicites.
"""

# ================================================================
# INITIALISATION VERTEX AI
# ================================================================

@st.cache_resource
def initialize_vertex_ai():
            """Initialise Vertex AI avec Service Account"""
            try:
                            service_account_json = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
                            if not service_account_json:
                                                st.error("❌ GCP_SERVICE_ACCOUNT_JSON manquant")
                                                st.stop()

                            credentials_dict = json.loads(service_account_json)
                            credentials = service_account.Credentials.from_service_account_info(
                                credentials_dict
                            )

        project_id = credentials_dict.get("project_id")
        if not project_id:
                            st.error("❌ project_id introuvable")
                            st.stop()

        vertexai.init(project=project_id, credentials=credentials)
        return project_id, credentials

except Exception as e:
        st.error(f"❌ Erreur Vertex AI: {str(e)}")
        st.stop()


@st.cache_resource
def get_search_client():
            """Retourne le client Discovery Engine"""
            try:
                            return SearchServiceClient()
except Exception as e:
        logger.error(f"Erreur SearchServiceClient: {str(e)}")
        return None


# ================================================================
# MOTEUR RAG - RECHERCHE DANS LE DATA STORE
# ================================================================

def search_datastore(
            query: str,
            doc_type_filter: Optional[str] = None,
            max_results: int = 5
) -> Tuple[List[Dict], str]:
            """
                Recherche sémantique avec hiérarchie des normes
                    Région: EU
                        Filtre: hopital_id = iris_brugmann
                            """
            try:
                            client = get_search_client()
                            if not client:
                                                return [], "Erreur: Client Discovery Engine indisponible"

                            # Chemin de la ressource
                            serving_config = (
                    f"projects/{PROJECT_ID}/locations/{LOCATION}/"
                                                f"collections/default_collection/dataStores/{DATA_STORE_ID}"
                            )

        # Filtre
        filter_str = f'hospital_id = "{HOSPITAL_FILTER}"'
        if doc_type_filter:
                            filter_str += f' AND doc_type = "{doc_type_filter}"'

        # Requête
        request = discoveryengine_v1.SearchRequest(
                            serving_config=serving_config,
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

        # Extraction
        documents = []
        for result in response.results:
                            doc = result.document
                            struct_data = doc.struct_data if hasattr(doc, 'struct_data') else {}

            doc_entry = {
                                    'filename': struct_data.get('file_name', 'Sans titre'),
                                    'doc_type': struct_data.get('doc_type', 'Protocole'),
                                    'url': doc.uri if hasattr(doc, 'uri') else "",
                                    'snippet': result.snippet.snippet_status if hasattr(result, 'snippet') else "",
                                    'relevance_score': getattr(result, 'relevance_score', 0.0),
                                    'hierarchy_priority': DOC_TYPE_HIERARCHY.get(
                                                                struct_data.get('doc_type', 'Protocole'), 0
                                    )
            }
            documents.append(doc_entry)

        # TRI: Hiérarchie > Pertinence
        documents.sort(
                            key=lambda x: (-x['hierarchy_priority'], -x['relevance_score'])
        )

        # Context formaté
        context = "## 📚 DOCUMENTS PERTINENTS (Hiérarchie belge appliquée)\n---\n"
        for idx, doc in enumerate(documents, 1):
                            context += f"\n**[DOC-{idx}] {doc['filename']}** ({doc['doc_type']})\n"
                            context += f"• Pertinence: {doc['relevance_score']:.0%}\n"
                            context += f"• Contenu: {doc['snippet'][:400]}...\n"
                        context += "\n---\n"

        logger.info(f"✓ {len(documents)} docs trouvés")
        return documents, context

except Exception as e:
        logger.error(f"❌ Erreur search_datastore: {str(e)}")
        return [], f"Erreur recherche: {str(e)}"


def call_gemini_with_rag(
            prompt: str,
            model_name: str,
            rag_context: str
) -> str:
            """
                Appelle Gemini avec RAG + Règle de faveur
                    Temperature: 0.1
                        """
    try:
                    augmented_prompt = f"""{SYSTEM_PROMPT}

                    {rag_context}

                    ## 📌 QUESTION
                    {prompt}

                    ⚠️ Rappel: Applique la RÈGLE DE FAVEUR et la HIÉRARCHIE BELGE.
                    """

        model = GenerativeModel(model_name=model_name)
        response = model.generate_content(
                            augmented_prompt,
                            generation_config={
                                                    "max_output_tokens": 2048,
                                                    "temperature": 0.1,
                            }
        )

        return response.text if response.text else "Pas de réponse"

except Exception as e:
        logger.error(f"Erreur Gemini: {str(e)}")
        return f"Erreur: {str(e)}"


# ================================================================
# INITIALISATION
# ================================================================

project_id, _ = initialize_vertex_ai()

# ================================================================
# UI - INTERFACE PRINCIPALE
# ================================================================

st.title("⚖️ NExUS v2.5")
st.markdown("**Assistant juridique - Protocoles CHU Brugmann**")
st.markdown(f"🇪🇺 Région: EU | 📊 Projet: {project_id}")
st.divider()

# SIDEBAR
with st.sidebar:
            st.header("⚙️ Configuration")

    model = st.selectbox(
                    "Modèle Gemini:",
                    ["gemini-2.0-flash", "gemini-1.5-pro"],
                    index=0
    )

    st.divider()
    st.subheader("🔍 Recherche")

    doc_filter = st.selectbox(
                    "Filtrer par type:",
                    ["Tous", "Loi", "CCT", "Protocole"],
                    index=0
    )
    doc_type = None if doc_filter == "Tous" else doc_filter

    max_docs = st.slider("Docs à consulter:", 1, 10, 5)

    st.divider()
    st.info("⚖️ **Règle de faveur**: ACTIVE")
    st.info("🇧🇪 **Hiérarchie**: Loi > CCT > Protocole")
    st.info("🔒 **Temperature**: 0.1 (Rigueur)")

# ZONE CHAT
st.subheader("💬 Posez votre question")

# Historique
if "messages" not in st.session_state:
            st.session_state.messages = []

# Afficher historique
for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                            st.markdown(msg["content"])

# Chat input
user_input = st.chat_input(
            "Ex: Quels sont mes droits de formation professionnelle?",
            key="chat_input"
)

if user_input:
            # Ajouter à l'historique
            st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
                    st.markdown(user_input)

    # Recherche + Analyse
    with st.chat_message("assistant"):
                    with st.spinner("🔍 Recherche dans les protocoles..."):
                                        documents, rag_context = search_datastore(
                                                                query=user_input,
                                                                doc_type_filter=doc_type,
                                                                max_results=max_docs
                                        )

                    if documents:
                                        with st.spinner("⏳ Analyse (Gemini, Règle de faveur)..."):
                                                                response = call_gemini_with_rag(
                                                                                            prompt=user_input,
                                                                                            model_name=model,
                                                                                            rag_context=rag_context
                                                                )

                                        st.markdown(response)

            # Sources
                        st.markdown("---")
            st.subheader("📚 Sources consultées")

            for idx, doc in enumerate(documents, 1):
                                    icon = "⚖️" if doc['doc_type'] == "Loi" else "📋" if doc['doc_type'] == "CCT" else "📄"
                                    st.markdown(
                                        f"{icon} **[DOC-{idx}]** {doc['filename']} "
                                        f"*({doc['doc_type']})* — {doc['relevance_score']:.0%}"
                                    )

            # Sauvegarde
            st.session_state.messages.append({"role": "assistant", "content": response})
else:
            st.warning("⚠️ Aucun document trouvé")

st.divider()
st.caption("NExUS v2.5 | Région EU | Hiérarchie belge | Règle de faveur")
