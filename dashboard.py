"""
NExUS v2.5 - Dashboard Principal
Interroge les 520 protocoles du CHU Brugmann via Vertex AI Discovery Engine (Région EU)
Hiérarchie belge: Loi > CCT > Protocole | Règle de faveur appliquée
"""

import streamlit as st
import json
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import discoveryengine_v1
from google.cloud.discoveryengine_v1.services.search_service import SearchServiceClient

# PAGE CONFIG
st.set_page_config(
                page_title="NExUS v2.5 - CHU Brugmann",
                page_icon="⚖️",
                layout="wide",
                initial_sidebar_state="expanded"
)

# CONFIGURATION GLOBALE
PROJECT_ID = "syndicat-novembre-2025"
LOCATION = "eu"  # RÉGION EUROPE
DATA_STORE_ID = "nexus-cgsp-pdf-global"
HOSPITAL_FILTER = "iris_brugmann"

# Hiérarchie des normes belges
HIERARCHY = {"Loi": 3, "CCT": 2, "Protocole": 1}

# ============ INITIALISATION VERTEX AI ============
@st.cache_resource
def init_vertex_ai():
                try:
                                    sa_json = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
                                    if not sa_json:
                                                            st.error("❌ GCP_SERVICE_ACCOUNT_JSON manquant")
                                                            st.stop()

                                    creds_dict = json.loads(sa_json)
                                    creds = service_account.Credentials.from_service_account_info(creds_dict)
                                    project = creds_dict.get("project_id")

        if not project:
                                st.error("❌ project_id introuvable")
                                st.stop()

        vertexai.init(project=project, credentials=creds)
        return project
except Exception as e:
        st.error(f"❌ Vertex AI: {str(e)}")
        st.stop()

# ============ DISCOVERY ENGINE CLIENT ============
@st.cache_resource
def get_search_client():
                try:
                                    return SearchServiceClient()
except Exception as e:
        st.error(f"❌ Search Client: {str(e)}")
        return None

# ============ RECHERCHE DANS LE DATA STORE ============
def search_docs(query: str, doc_type: str = None, max_results: int = 5):
                """Recherche sémantique avec tri par hiérarchie"""
                client = get_search_client()
                if not client:
                                    return [], "❌ Client indisponible"

                try:
                                    serving_config = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}"

        filter_str = f'hospital_id = "{HOSPITAL_FILTER}"'
        if doc_type and doc_type != "Tous":
                                filter_str += f' AND doc_type = "{doc_type}"'

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
        docs = []

        for result in response.results:
                                doc = result.document
                                struct = doc.struct_data if hasattr(doc, 'struct_data') else {}

            doc_type_val = struct.get('doc_type', 'Protocole')
            docs.append({
                                        'filename': struct.get('file_name', 'Sans titre'),
                                        'doc_type': doc_type_val,
                                        'snippet': result.snippet.snippet_status if hasattr(result, 'snippet') else "",
                                        'score': getattr(result, 'relevance_score', 0.0),
                                        'priority': HIERARCHY.get(doc_type_val, 0)
            })

        # TRI: Hiérarchie puis pertinence
        docs.sort(key=lambda x: (-x['priority'], -x['score']))

        # Contexte formaté
        ctx = "## 📚 DOCUMENTS PERTINENTS (Hiérarchie belge)\n---\n"
        for i, d in enumerate(docs, 1):
                                ctx += f"\n**[DOC-{i}] {d['filename']}** ({d['doc_type']})\n"
                                ctx += f"• Pertinence: {d['score']:.0%}\n"
                                ctx += f"• Extrait: {d['snippet'][:350]}...\n"
                            ctx += "\n---\n"

        return docs, ctx
except Exception as e:
        return [], f"❌ Erreur: {str(e)}"

# ============ APPEL GEMINI AVEC RAG ============
def gemini_rag(question: str, model: str, context: str):
                """Appelle Gemini avec contexte RAG + Règle de faveur"""
                try:
                                    system = """Tu es NExUS, assistant juridique pour délégués syndicaux CHU Brugmann.

                                    RÈGLES ABSOLUES:
                                    1. ⚖️ RÈGLE DE FAVEUR: Interprète TOUJOURS en faveur du travailleur
                                    2. 🇧🇪 HIÉRARCHIE: Loi > CCT > Protocole (applique cet ordre)
                                    3. 📋 SOURCES: Cite [DOC-1], [DOC-2]... obligatoirement
                                    4. ❌ PAS D'INVENTION: Réponds UNIQUEMENT sur documents fournis
                                    5. 💯 RIGUEUR: Zéro hallucination

                                    Structure: titres, listes, références explicites."""

        prompt = f"""{system}

        {context}

        ## QUESTION
        {question}

        ⚠️ Applique RÈGLE DE FAVEUR et HIÉRARCHIE BELGE."""

        gmodel = GenerativeModel(model)
        resp = gmodel.generate_content(
                                prompt,
                                generation_config={"max_output_tokens": 2048, "temperature": 0.1}
        )
        return resp.text if resp.text else "Pas de réponse"
except Exception as e:
        return f"❌ Gemini: {str(e)}"

# ============ INIT ============
project_id = init_vertex_ai()

# ============ UI ============
st.title("⚖️ NExUS v2.5")
st.markdown("**Protocoles CHU Brugmann | Région EU | Hiérarchie belge**")
st.divider()

# SIDEBAR
with st.sidebar:
                st.header("⚙️ Config")
                model = st.selectbox("Gemini:", ["gemini-2.0-flash", "gemini-1.5-pro"], index=0)
                doc_filter = st.selectbox("Type:", ["Tous", "Loi", "CCT", "Protocole"], index=0)
                max_docs = st.slider("Docs:", 1, 10, 5)
                st.divider()
                st.info("✅ Vertex AI init")
                st.info("⚖️ Règle faveur: ACTIVE")
                st.info("🇧🇪 Hiérarchie: Loi > CCT > Protocole")
                st.info("🔒 Temperature: 0.1")

# HISTORIQUE
if "messages" not in st.session_state:
                st.session_state.messages = []

# AFFICHER HISTORIQUE
for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                                    st.markdown(msg["content"])

            # CHAT INPUT EN BAS
            st.divider()
st.subheader("💬 Posez votre question")

user_input = st.chat_input("Quels sont mes droits...?")

if user_input:
                # Ajouter user
                st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
                        st.markdown(user_input)

    # Recherche + Analyse
    with st.chat_message("assistant"):
                        with st.spinner("🔍 Recherche..."):
                                                docs, context = search_docs(user_input, doc_filter, max_docs)

                        if docs:
                                                with st.spinner("⏳ Gemini analyse (Règle faveur)..."):
                                                                            response = gemini_rag(user_input, model, context)

                                                st.markdown(response)

            # SOURCES
                            st.markdown("---")
            st.subheader("📚 Sources consultées")
            for i, d in enumerate(docs, 1):
                                        icon = "⚖️" if d['doc_type'] == "Loi" else "📋" if d['doc_type'] == "CCT" else "📄"
                                        st.markdown(f"{icon} **[DOC-{i}]** {d['filename']} ({d['doc_type']}) — {d['score']:.0%}")

            # Sauvegarde
            st.session_state.messages.append({"role": "assistant", "content": response})
else:
            st.warning("⚠️ Aucun document trouvé")

st.divider()
st.caption(f"NExUS v2.5 | {project_id} | Région EU | Hiérarchie belge | Règle de faveur")
