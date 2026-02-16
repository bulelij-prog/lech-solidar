"""
NEXUS - Système RAG Hybride pour CHU Brugmann
Gemini (chat) + Discovery Engine (recherche documentaire)
Hiérarchie légale belge + Règle de Faveur
"""

import streamlit as st
import google.generativeai as genai
import json
from google.cloud import discoveryengine_v1
from google.oauth2 import service_account
from typing import List, Dict

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="NEXUS - CHU Brugmann RAG",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ NEXUS - Système d'Aide Juridique (CHU Brugmann)")
st.markdown("**Recherche RAG + Conseil Gemini avec hiérarchie légale belge et règle de faveur**")

# ==================== SIDEBAR DIAGNOSTIC ====================
with st.sidebar:
    st.header("🔧 DIAGNOSTIC & CONFIGURATION")
    st.divider()

    # CHECK 1: Secrets
    st.subheader("1️⃣ Configuration Secrets")

    api_key_ok = False
    gcp_json_ok = False

    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if api_key:
            st.success(f"✅ GOOGLE_API_KEY found ({len(api_key)} chars)")
            api_key_ok = True
        else:
            st.error("❌ GOOGLE_API_KEY NOT found")
    except Exception as e:
        st.error(f"❌ Error reading GOOGLE_API_KEY: {str(e)[:50]}")

    try:
        gcp_json_str = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
        if gcp_json_str:
            try:
                gcp_json = json.loads(gcp_json_str)
                st.success("✅ GCP_SERVICE_ACCOUNT_JSON found (valid JSON)")
                gcp_json_ok = True
            except json.JSONDecodeError:
                st.error("❌ GCP_SERVICE_ACCOUNT_JSON: Invalid JSON format")
        else:
            st.error("❌ GCP_SERVICE_ACCOUNT_JSON NOT found")
    except Exception as e:
        st.error(f"❌ Error reading GCP_SERVICE_ACCOUNT_JSON: {str(e)[:50]}")

    st.divider()

    # CHECK 2: Gemini Connection
    st.subheader("2️⃣ Gemini Connection")

    gemini_ok = False
    try:
        if api_key_ok:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            available_models = [
                m.name.replace("models/", "") for m in models
                if "generateContent" in m.supported_generation_methods
            ]
            st.success(f"✅ Gemini API: {len(available_models)} models available")
            gemini_ok = True
        else:
            st.error("❌ Cannot test Gemini: API key missing")
    except Exception as e:
        st.error(f"❌ Gemini test failed: {str(e)[:50]}")

    st.divider()

    # CHECK 3: Discovery Engine Credentials
    st.subheader("3️⃣ Discovery Engine Connection")

    discovery_ok = False
    try:
        if gcp_json_ok:
            try:
                gcp_json_check = json.loads(st.secrets.get("GCP_SERVICE_ACCOUNT_JSON"))
                credentials_check = service_account.Credentials.from_service_account_info(gcp_json_check)
                st.success("✅ GCP credentials: Successfully created from JSON")
                discovery_ok = True
            except Exception as e:
                st.error(f"❌ GCP credentials creation failed: {str(e)[:80]}")
        else:
            st.error("❌ Cannot test Discovery Engine: GCP JSON missing")
    except Exception as e:
        st.error(f"❌ Discovery Engine setup error: {str(e)[:50]}")

    st.divider()

    # Model selector
    st.subheader("📌 Gemini Model")
    if gemini_ok:
        model_choice = st.selectbox(
            "Choose model:",
            ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
            index=0
        )
        st.info(f"Selected: **{model_choice}**")
    else:
        st.warning("Cannot select model: Gemini connection failed")
        model_choice = "gemini-2.0-flash"

    # Discovery Engine parameters
    st.subheader("🔍 Discovery Engine Settings")
    project_id = "syndicat-novembre-2025"
    datastore_id = "nexus-cgsp-pdf-global"
    st.caption(f"Project: `{project_id}`")
    st.caption(f"DataStore: `{datastore_id}`")
    location = st.selectbox("Region:", ["global", "eu"], index=0)

    st.divider()

    # Status summary
    all_ok = api_key_ok and gcp_json_ok and gemini_ok and discovery_ok
    if all_ok:
        st.success("### 🟢 ALL SYSTEMS GO")
    else:
        st.warning("### 🟡 SOME CHECKS FAILED - See above")


# ==================== SYSTEM PROMPT ====================
SYSTEM_PROMPT = """Tu es un assistant juridique spécialisé en droit du travail belge pour les délégués syndicaux du CHU Brugmann.

**HIÉRARCHIE LÉGALE BELGE (Applique STRICTEMENT dans cet ordre):**
1. Loi belge fédérale (code du travail, conventions collectives nationales)
2. Conventions collectives du travail (CCT) sectorielles/entreprise
3. Protocoles internes du CHU Brugmann (consensuels)

**RÈGLE DE FAVEUR (Principe cardinal):**
En cas de conflit entre deux normes, applique toujours celle qui est PLUS FAVORABLE au travailleur/à la travailleuse.
Exemple: Si une CCT dit "30 jours de congé" mais la loi fédérale dit "25 jours", applique 30 jours.
Exemple 2: Si un protocole local dit "salaire minimum 2000€" mais la loi dit "2500€", applique 2500€.

**SOURCES & CITATIONS:**
- Cite TOUJOURS la source: "Loi du...", "CCT du...", "Article X du Protocole..."
- Si un document RAG contredit la loi belge, privilégie LA LOI et explique pourquoi.
- Inclus la section/article spécifique quand c'est possible.

**TRANSPARENCE:**
- Sois honnête sur ce que tu ignores.
- Si le document RAG ne contient pas l'information, dis-le explicitement.
- Conseille de consulter un juriste pour les cas complexes.
"""


# ==================== HELPER: Extract best available text ====================

def extract_document_data(result) -> Dict:
    """
    Extrait titre, contenu et source depuis un résultat Discovery Engine.
    Stratégie en cascade: derived_struct_data → struct_data → document.name → document.id
    """
    doc = result.document

    # --- Titre: cascade de fallbacks ---
    title = "Unknown"

    # Tentative 1: struct_data standard
    if doc.struct_data:
        title = (
            doc.struct_data.get("title")
            or doc.struct_data.get("name")
            or doc.struct_data.get("filename")
            or "Unknown"
        )

    # Tentative 2: derived_struct_data (extraits générés par Google pour les PDFs)
    derived = {}
    if doc.derived_struct_data:
        derived = dict(doc.derived_struct_data)
        if title == "Unknown":
            title = (
                derived.get("title")
                or derived.get("name")
                or "Unknown"
            )

    # Tentative 3: extraire le nom de fichier depuis doc.name (chemin GCS)
    if title == "Unknown" and doc.name:
        # doc.name ressemble à: projects/.../documents/abc123
        # ou la source GCS est dans struct_data.source_uri
        parts = doc.name.split("/")
        title = parts[-1] if parts else doc.id or "Unknown"

    # Tentative 4: utiliser l'ID du document comme titre de dernier recours
    if title == "Unknown" and doc.id:
        title = doc.id

    # --- Contenu: cascade derived → struct ---
    content = ""

    # derived_struct_data contient souvent "extractive_answers" ou "snippets" pour les PDFs
    if derived:
        # Extraits de réponse (extractive_answers)
        extractive_answers = derived.get("extractive_answers", [])
        if extractive_answers:
            content = " ".join([
                a.get("content", "") for a in extractive_answers
                if isinstance(a, dict)
            ])[:1500]

        # Snippets si pas d'extractive_answers
        if not content:
            snippets = derived.get("snippets", [])
            if snippets:
                content = " ".join([
                    s.get("snippet", "") for s in snippets
                    if isinstance(s, dict)
                ])[:1500]

        # Contenu brut dans derived
        if not content:
            content = derived.get("content", "")[:1500]

    # Fallback: struct_data classique
    if not content and doc.struct_data:
        content = (
            doc.struct_data.get("content", "")
            or doc.struct_data.get("text", "")
            or doc.struct_data.get("body", "")
        )[:1500]

    # --- Source URI ---
    source_uri = ""
    if doc.struct_data:
        source_uri = doc.struct_data.get("source_uri", "") or doc.struct_data.get("uri", "")
    if not source_uri and derived:
        source_uri = derived.get("source_uri", "") or derived.get("link", "")
    if not source_uri and doc.name:
        source_uri = doc.name

    return {
        "title": title,
        "content": content,
        "snippet": content[:300],
        "source_uri": source_uri,
        "doc_id": doc.id or "",
        "_raw_derived": derived,        # Gardé pour le debug temporaire
        "_raw_struct": dict(doc.struct_data) if doc.struct_data else {},
    }


# ==================== FUNCTIONS ====================

def query_discovery_engine(query: str, project_id: str, datastore_id: str, location: str) -> List[Dict]:
    """
    Interroge le Discovery Engine avec authentification explicite via service account.
    """
    try:
        gcp_json_str = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
        if not gcp_json_str:
            st.error("❌ GCP_SERVICE_ACCOUNT_JSON secret not found")
            return []

        try:
            gcp_json = json.loads(gcp_json_str)
        except json.JSONDecodeError as e:
            st.error(f"❌ GCP JSON parsing failed: {str(e)[:80]}")
            return []

        try:
            credentials = service_account.Credentials.from_service_account_info(gcp_json)
        except Exception as e:
            st.error(f"❌ Failed to create GCP credentials: {str(e)[:80]}")
            return []

        try:
            client = discoveryengine_v1.SearchServiceClient(credentials=credentials)
        except Exception as e:
            st.error(f"❌ Failed to initialize Discovery Engine client: {str(e)[:80]}")
            return []

        serving_config = (
            f"projects/{project_id}"
            f"/locations/{location}"
            f"/collections/default_collection"
            f"/dataStores/{datastore_id}"
            f"/servingConfigs/default_search"
        )

        request = discoveryengine_v1.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=5,
        )

        try:
            response = client.search(request)
        except Exception as e:
            st.error(f"❌ Discovery Engine search failed: {str(e)[:100]}")
            return []

        documents = []
        for result in response.results:
            try:
                doc_data = extract_document_data(result)
                documents.append(doc_data)
            except Exception as e:
                st.warning(f"⚠️ Error parsing one document: {str(e)[:50]}")
                continue

        # ============================================================
        # DEBUG TEMPORAIRE: Affiche la structure brute du 1er résultat
        # Supprime ce bloc dès que les titres s'affichent correctement
        # ============================================================
        if response.results:
            with st.expander("🔬 DEBUG - Structure brute du Document 1 (supprimer après diagnostic)", expanded=True):
                first_result = response.results[0]
                st.markdown("**`result.document` (objet complet):**")
                st.write(first_result.document)
                st.divider()
                st.markdown("**`struct_data` (clés disponibles):**")
                if first_result.document.struct_data:
                    st.json(dict(first_result.document.struct_data))
                else:
                    st.warning("struct_data est vide")
                st.divider()
                st.markdown("**`derived_struct_data` (clés disponibles):**")
                if first_result.document.derived_struct_data:
                    st.json(dict(first_result.document.derived_struct_data))
                else:
                    st.warning("derived_struct_data est vide")
                st.divider()
                st.markdown("**`document.name` et `document.id`:**")
                st.write(f"name: `{first_result.document.name}`")
                st.write(f"id: `{first_result.document.id}`")
        # ============================================================
        # FIN DEBUG TEMPORAIRE
        # ============================================================

        return documents

    except Exception as e:
        st.error(f"❌ Unexpected error in query_discovery_engine: {str(e)[:100]}")
        return []


def generate_response(user_input: str, rag_documents: List[Dict], model_choice: str) -> str:
    """
    Génère une réponse Gemini avec contexte RAG.
    """
    try:
        if rag_documents:
            context = "\\n---\\n**DOCUMENTS PERTINENTS (Discovery Engine):**\\n"
            for i, doc in enumerate(rag_documents, 1):
                context += f"\\n[Document {i}] {doc['title']}\\n"
                if doc['content']:
                    context += f"Contenu: {doc['content']}\\n"
                if doc['source_uri']:
                    context += f"Source: {doc['source_uri']}\\n"
        else:
            context = "\\n---\\n**Aucun document trouvé dans le Data Store.**\\n"

        full_prompt = f"""{SYSTEM_PROMPT}

---
QUESTION DE L'UTILISATEUR:
{user_input}

---
{context}

---
INSTRUCTION FINALE:
Réponds à la question en appliquant strictement:
1. La hiérarchie légale belge
2. La règle de faveur (favorise toujours le travailleur)
3. Les documents RAG comme référence (mais la loi prime)

Sois clair, structuré, et cite tes sources."""

        model = genai.GenerativeModel(model_choice)
        response = model.generate_content(full_prompt)
        return response.text if response.text else "Gemini returned empty response"

    except Exception as e:
        return f"❌ Error generating response: {str(e)[:100]}"


# ==================== MAIN CHAT INTERFACE ====================

st.divider()
st.header("💬 Assistant Juridique NEXUS")
st.markdown("Posez vos questions sur le droit du travail belge. Le système recherche dans vos 520 protocoles et applique la règle de faveur.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📄 Sources"):
                for source in message["sources"]:
                    st.markdown(f"- **{source['title']}**: {source['source_uri']}")

if user_input := st.chat_input("Posez votre question juridique..."):

    if not all_ok:
        st.error("⚠️ System not fully configured. Check sidebar for issues.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.spinner("🔍 Searching Discovery Engine (520 protocoles)..."):
        rag_documents = query_discovery_engine(user_input, project_id, datastore_id, location)

    with st.spinner("⚙️ Gemini analyse et applique la règle de faveur..."):
        response_text = generate_response(user_input, rag_documents, model_choice)

    with st.chat_message("assistant"):
        st.markdown(response_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "sources": rag_documents
    })

    if rag_documents:
        with st.expander(f"📊 RAG Context ({len(rag_documents)} documents trouvés)"):
            for i, doc in enumerate(rag_documents, 1):
                st.subheader(f"Document {i}: {doc['title']}")
                st.write(f"**Source:** {doc['source_uri']}")
                st.write(f"**Extrait:** {doc['snippet']}")


# ==================== FOOTER ====================
st.divider()
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Messages", len(st.session_state.messages))
with col2:
    st.metric("Streamlit", st.__version__)
with col3:
    st.metric("Mode", "HYBRID RAG+GEMINI")

st.caption("NEXUS v2.3 | Hybride Gemini + Discovery Engine | Hiérarchie belge + Règle de Faveur")
