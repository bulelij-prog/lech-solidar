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

    # Discovery Engine parameters (fixed values, not editable)
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


# ==================== FUNCTIONS ====================

def query_discovery_engine(query: str, project_id: str, datastore_id: str, location: str) -> List[Dict]:
    """
    Interroge le Discovery Engine avec authentification explicite via service account.
    FIX: st.debug() supprimé, credentials passés explicitement au client.
    """
    try:
        # Step 1: Get JSON from secrets
        gcp_json_str = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
        if not gcp_json_str:
            st.error("❌ GCP_SERVICE_ACCOUNT_JSON secret not found")
            return []

        # Step 2: Parse JSON
        try:
            gcp_json = json.loads(gcp_json_str)
        except json.JSONDecodeError as e:
            st.error(f"❌ GCP JSON parsing failed: {str(e)[:80]}")
            return []

        # Step 3: Create credentials from service account info
        try:
            credentials = service_account.Credentials.from_service_account_info(gcp_json)
        except Exception as e:
            st.error(f"❌ Failed to create GCP credentials: {str(e)[:80]}")
            return []

        # Step 4: Initialize client WITH explicit credentials (fixes 503 error)
        try:
            client = discoveryengine_v1.SearchServiceClient(credentials=credentials)
        except Exception as e:
            st.error(f"❌ Failed to initialize Discovery Engine client: {str(e)[:80]}")
            return []

        # Step 5: Build serving config path
        serving_config = (
            f"projects/{project_id}"
            f"/locations/{location}"
            f"/collections/default_collection"
            f"/dataStores/{datastore_id}"
            f"/servingConfigs/default_search"
        )

        # Step 6: Build and execute search request
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

        # Step 7: Extract results
        documents = []
        for result in response.results:
            try:
                struct_data = result.document.struct_data if result.document.struct_data else {}
                doc_info = {
                    "title": struct_data.get("title", "Unknown"),
                    "snippet": struct_data.get("snippet", "")[:500],
                    "content": struct_data.get("content", "")[:1000],
                    "source_uri": struct_data.get("source_uri", ""),
                }
                documents.append(doc_info)
            except Exception:
                continue

        return documents

    except Exception as e:
        st.error(f"❌ Unexpected error in query_discovery_engine: {str(e)[:100]}")
        return []


def generate_response(user_input: str, rag_documents: List[Dict], model_choice: str) -> str:
    """
    Génère une réponse Gemini avec contexte RAG.
    FIX: paramètre renommé user_input pour cohérence avec l'appel.
    """
    try:
        # Build context from RAG results
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

        # Build full prompt
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

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📄 Sources"):
                for source in message["sources"]:
                    st.markdown(f"- **{source['title']}**: {source['source_uri']}")

# Chat input — FIX: variable nommée user_input partout, cohérence garantie
if user_input := st.chat_input("Posez votre question juridique..."):

    if not all_ok:
        st.error("⚠️ System not fully configured. Check sidebar for issues.")
        st.stop()

    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Query Discovery Engine
    with st.spinner("🔍 Searching Discovery Engine (520 protocoles)..."):
        rag_documents = query_discovery_engine(user_input, project_id, datastore_id, location)

    # Generate Gemini response — FIX: user_input passé ici (plus user_query)
    with st.spinner("⚙️ Gemini analyse et applique la règle de faveur..."):
        response_text = generate_response(user_input, rag_documents, model_choice)

    # Display assistant response
    with st.chat_message("assistant"):
        st.markdown(response_text)

    # Store in session history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "sources": rag_documents
    })

    # Show RAG context in expander
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

st.caption("NEXUS v2.2 | Hybride Gemini + Discovery Engine | Hiérarchie belge + Règle de Faveur")
