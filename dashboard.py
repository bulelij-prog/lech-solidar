"""
NExUS v2.5 - Étape A (RAG Integration)
Interface Streamlit + Gemini + Discovery Engine
Recherche documentaire avec sources citées
"""

import streamlit as st
import google.generativeai as genai
from google.cloud import discoveryengine_v1
from google.api_core.gapic_v1 import client_info as grpc_client_info
import os

# PAGE CONFIG
st.set_page_config(
              page_title="NExUS v2.5 - Étape A (RAG)",
              page_icon="⚖️",
              layout="wide",
              initial_sidebar_state="expanded"
)

# CONFIGURATION DISCOVERY ENGINE
PROJECT_ID = "syndicat-novembre-2025"
LOCATION = "global"
DATA_STORE_ID = "nexus-cgsp-pdf-global"

# INIT GEMINI
@st.cache_resource
def init_gemini():
              """Initialize Gemini API"""
              try:
                                api_key = st.secrets.get("GOOGLE_API_KEY")
                                if not api_key:
                                                      st.error("❌ GOOGLE_API_KEY manquant dans Streamlit Secrets")
                                                      st.stop()
                                                  genai.configure(api_key=api_key)
                                return True
except Exception as e:
        st.error(f"❌ Erreur Gemini: {str(e)}")
        return False

# SEARCH DISCOVERY ENGINE
def search_documents(query: str, max_results: int = 5) -> list:
              """Search documents in Discovery Engine Data Store"""
              try:
                                client = discoveryengine_v1.SearchServiceClient()

        # Build search request
                  request = discoveryengine_v1.SearchRequest(
                                        serving_config=f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/servingConfigs/default_config",
                                        query=query,
                                        page_size=max_results,
                                        content_search_spec=discoveryengine_v1.SearchRequest.ContentSearchSpec(
                                                                  snippet_spec=discoveryengine_v1.SearchRequest.ContentSearchSpec.SnippetSpec(
                                                                                                return_snippet=True,
                                                                  ),
                                                                  summary_spec=discoveryengine_v1.SearchRequest.ContentSearchSpec.SummarySpec(
                                                                                                summary_result_count=3,
                                                                                                include_citations=True,
                                                                  ),
                                        ),
                  )

        response = client.search(request)

        results = []
        for result in response.results:
                              doc_title = result.document.derived_struct_data.get("title", "Sans titre")
                              snippet = result.document.derived_struct_data.get("snippets", [{}])[0].get("snippet", "")
                              doc_uri = result.document.derived_struct_data.get("link", "")

            results.append({
                                      "title": doc_title,
                                      "snippet": snippet,
                                      "uri": doc_uri,
                                      "relevance": result.relevance_score if hasattr(result, 'relevance_score') else 0.0
            })

        return results
except Exception as e:
        st.warning(f"⚠️ Erreur lors de la recherche: {str(e)}")
        return []

# AUGMENT PROMPT WITH RAG
def augment_prompt_with_rag(user_query: str, rag_docs: list) -> str:
              """Build augmented prompt with RAG documents"""
    if not rag_docs:
                      return user_query

    context = "\n\nDocuments trouvés:\n"
    for i, doc in enumerate(rag_docs, 1):
                      context += f"\n{i}. **{doc['title']}**\n"
                      if doc['snippet']:
                                            context += f"   Extrait: {doc['snippet'][:200]}...\n"
                                        if doc['uri']:
                                                              context += f"   Lien: {doc['uri']}\n"

    augmented = f"Basé sur ces documents officiels:\n{context}\n\nQuestion: {user_query}"
    return augmented

# CALL GEMINI WITH CONTEXT
def call_gemini_rag(prompt: str, model: str = "gemini-1.5-flash") -> str:
              """Send augmented prompt to Gemini"""
    try:
                      gmodel = genai.GenerativeModel(model)
        resp = gmodel.generate_content(prompt)
        return resp.text if resp.text else "Pas de réponse"
except Exception as e:
        return f"Erreur Gemini: {str(e)}"

# INIT
if not init_gemini():
              st.stop()

# UI TITLE
st.title("⚖️ NExUS v2.5 - Étape A (RAG)")
st.markdown("**Recherche intelligente avec Discovery Engine + Gemini**")
st.markdown("🔍 Les réponses sont basées sur 520 documents légaux officiels")

# SIDEBAR
with st.sidebar:
              st.header("⚙️ Configuration")
    st.success("✅ Gemini API configured")
    st.info("📚 Data Store: 520 documents légaux")
    use_rag = st.checkbox("Utiliser RAG (Discovery Engine)", value=True)
    max_results = st.slider("Nombre de documents à récupérer", 1, 10, 5)
    model_choice = st.selectbox(
                      "Gemini Model:",
                      ["gemini-1.5-flash", "gemini-1.5-pro"],
                      index=0
    )

# SESSION STATE
if "messages" not in st.session_state:
              st.session_state.messages = []
if "rag_results" not in st.session_state:
              st.session_state.rag_results = []

# DISPLAY CONVERSATION
st.subheader("💬 Conversation")
st.divider()

for message in st.session_state.messages:
              with st.chat_message(message["role"]):
                                st.markdown(message["content"])
                                # Show RAG sources if available
                                if message.get("sources"):
                                                      with st.expander("📚 Sources utilisées"):
                                                                                for source in message["sources"]:
                                                                                                              st.markdown(f"**{source['title']}**")
                                                                                                              if source['snippet']:
                                                                                                                                                st.caption(source['snippet'][:150] + "...")
                                                                                                                        
                                                                                          # CHAT INPUT
                                                                                          user_input = st.chat_input("Posez une question sur les protocoles et lois syndicales...")

                                          if user_input:
                                                        # Add user message
                                                        st.session_state.messages.append({
                                                                          "role": "user",
                                                                          "content": user_input
                                                        })

    with st.chat_message("user"):
                      st.markdown(user_input)

    # PROCESS WITH RAG
    with st.chat_message("assistant"):
                      status = st.status("Traitement...", expanded=True)

        rag_docs = []
        augmented_prompt = user_input

        if use_rag:
                              status.write("🔍 Recherche dans Discovery Engine...")
                              rag_docs = search_documents(user_input, max_results)
                              if rag_docs:
                                                        status.write(f"✅ {len(rag_docs)} document(s) trouvé(s)")
                                                        augmented_prompt = augment_prompt_with_rag(user_input, rag_docs)
        else:
                status.write("⚠️ Aucun document trouvé, utilisation de Gemini seul")

        status.write("💭 Génération de la réponse par Gemini...")
        response = call_gemini_rag(augmented_prompt, model_choice)
        status.update(label="✅ Complété", state="complete")

        st.markdown(response)

        # Show sources
        if rag_docs:
                              with st.expander("📚 Sources utilisées"):
                                                        for doc in rag_docs:
                                                                                      st.markdown(f"**{doc['title']}** (Pertinence: {doc['relevance']:.1%})")
                                                                                      if doc['snippet']:
                                                                                                                        st.caption(doc['snippet'][:200] + "...")
                                                                                                                    if doc['uri']:
                                                                                                                                                      st.markdown(f"[Voir le document]({doc['uri']})")
                                                                                                                                  
                                                                      # Add to history with sources
                                                                      st.session_state.messages.append({
                                                "role": "assistant",
                                                "content": response,
                                                "sources": rag_docs
                                                        })

                  # FOOTER
                  st.divider()
st.caption("NExUS v2.5 - Étape A | Streamlit + Gemini + Discovery Engine | RAG Integration")
