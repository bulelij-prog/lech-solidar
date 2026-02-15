"""
NExUS v2.5 - Dashboard avec RAG (Retrieval Augmented Generation)
Utilise Vertex AI Discovery Engine pour les protocoles CHU Brugmann
"""

import streamlit as st
import json
from datetime import datetime
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel
from rag_engine import RAGEngine, initialize_rag_engine

# ============================================================
# CONFIGURATION STREAMLIT
# ============================================================

st.set_page_config(
      page_title="NExUS v2.5 - RAG Dashboard",
      page_icon="⚖️",
      layout="wide",
      initial_sidebar_state="expanded"
)

# ============================================================
# INITIALISATION VERTEX AI AVEC SERVICE ACCOUNT
# ============================================================

@st.cache_resource
def initialize_vertex_ai():
      """
          Initialise Vertex AI avec credentials du Service Account

                  Returns:
                          tuple: (project_id, credentials)
                              """
      try:
                service_account_json = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
                if not service_account_json:
                              st.error("❌ Erreur: GCP_SERVICE_ACCOUNT_JSON non configuré")
                              st.error("Ajoute-le dans Streamlit Secrets")
                              st.stop()

                try:
                              credentials_dict = json.loads(service_account_json)
      except json.JSONDecodeError:
                    st.error("❌ Erreur: GCP_SERVICE_ACCOUNT_JSON n'est pas un JSON valide")
                    st.stop()

          credentials = service_account.Credentials.from_service_account_info(
                        credentials_dict
          )

        project_id = credentials_dict.get("project_id")
        if not project_id:
                      st.error("❌ Erreur: Impossible de récupérer le project_id")
                      st.stop()

        vertexai.init(project=project_id, credentials=credentials)
        return project_id, credentials

except Exception as e:
        st.error(f"❌ Erreur d'initialisation Vertex AI: {str(e)}")
        st.stop()


@st.cache_resource
def get_rag_engine():
      """Initialise le moteur RAG"""
    return initialize_rag_engine()


# ============================================================
# FONCTIONS GEMINI + RAG
# ============================================================

def call_gemini_with_rag(
      prompt: str,
      model_name: str,
      rag_context: str,
      documents: list
) -> str:
      """
          Appelle Gemini en augmentant le prompt avec le contexte RAG

                  Args:
                          prompt: Prompt utilisateur
                                  model_name: Modèle Gemini
                                          rag_context: Contexte enrichi du RAG
                                                  documents: Liste des documents trouvés

                                                              Returns:
                                                                      str: Réponse du modèle
                                                                          """
    try:
              # Construction du prompt augmenté
              augmented_prompt = f"""{rag_context}

              ## 📋 QUESTION UTILISATEUR
              {prompt}

              ## 📌 INSTRUCTIONS
              - Réponds UNIQUEMENT en te basant sur les documents ci-dessus
              - Si l'information n'est pas dans les documents, dis-le clairement
              - Cite toujours tes sources (numéro du document)
              - Structure ta réponse avec des titres et des listes
              """

        model = GenerativeModel(model_name=model_name)
        response = model.generate_content(
                      augmented_prompt,
                      generation_config={
                                        "max_output_tokens": 2048,
                                        "temperature": 0.5,  # Plus conservateur pour RAG
                      }
        )

        return response.text if response.text else "Pas de réponse disponible"

except Exception as e:
        return f"Erreur Gemini: {str(e)}"


# ============================================================
# INITIALISATION AU DÉMARRAGE
# ============================================================

project_id, credentials = initialize_vertex_ai()
rag_engine = get_rag_engine()

st.success(f"✓ Vertex AI + RAG initialisés - Projet: {project_id}")

# ============================================================
# INTERFACE STREAMLIT
# ============================================================

st.title("⚖️ NExUS v2.5 - RAG Dashboard")
st.markdown("**Assistant IA Expert - Secteur Aide aux Personnes | CHU Brugmann**")
st.divider()

# SIDEBAR - Configuration
with st.sidebar:
      st.header("⚙️ Configuration RAG")

    model_choice = st.selectbox(
              "Choisir le modèle Gemini:",
              ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
              index=0
    )

    temperature = st.slider(
              "Température (créativité):",
              min_value=0.0,
              max_value=1.0,
              value=0.5,  # Plus bas pour RAG
              step=0.1
    )

    st.divider()

    st.subheader("🔍 Filtres RAG")
    doc_type = st.selectbox(
              "Type de document:",
              ["Tous", "Protocole", "CCT", "Loi"],
              index=0
    )
    doc_type_filter = None if doc_type == "Tous" else doc_type

    max_results = st.slider(
              "Nombre de documents:",
              min_value=1,
              max_value=10,
              value=5,
              step=1
    )

    st.divider()
    st.info(f"📊 Projet: `{project_id}`")

# ZONE PRINCIPALE - Chat RAG
col1, col2 = st.columns([2, 1])

with col1:
      st.subheader("💬 Testeur RAG + Gemini")

    prompt = st.text_area(
              "Posez votre question juridique:",
              placeholder="Ex: Quelle est la politique de formation professionnelle?",
              height=150,
              key="user_prompt"
    )

    if st.button("🔍 Rechercher + Analyser", use_container_width=True):
              if prompt.strip():
                            with st.spinner("⏳ Recherche dans les protocoles..."):
                                              # ÉTAPE 1: Recherche RAG
                                              documents, rag_context = rag_engine.search_datastore(
                                                                    query=prompt,
                                                                    doc_type_filter=doc_type_filter,
                                                                    max_results=max_results
                                              )

                if documents:
                                      st.success(f"✓ {len(documents)} documents trouvés")

                    with st.spinner("⏳ Gemini analyse les documents..."):
                                              # ÉTAPE 2: Appel Gemini avec RAG
                                              response = call_gemini_with_rag(
                                                                            prompt=prompt,
                                                                            model_name=model_choice,
                                                                            rag_context=rag_context,
                                                                            documents=documents
                                              )

                        # Affichage de la réponse
                                              st.success("✓ Analyse complète")
                        st.markdown("---")
                        st.write(response)

                        # Affichage des sources
                        st.markdown("---")
                        st.subheader("📚 Sources consultées")

                        sources = rag_engine.get_sources_list(documents)
                        for idx, source in enumerate(sources, 1):
                                                      relevance = documents[idx-1].get('relevance_score', 0)
                                                      st.markdown(
                                                          f"**{idx}.** {source} "
                                                          f"(*Score: {relevance:.1%}*)"
                                                      )

                        # Sauvegarde dans l'historique
                        if "chat_history" not in st.session_state:
                                                      st.session_state.chat_history = []

                        st.session_state.chat_history.append({
                                                      "prompt": prompt,
                                                      "response": response,
                                                      "sources": sources,
                                                      "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
else:
                    st.warning("⚠️ Aucun document trouvé pour cette recherche")
else:
            st.warning("⚠️ Veuillez entrer une question")

with col2:
      st.subheader("📈 Stats")
    st.metric(
              "Modèle Actif",
              model_choice.split("-")[1]
    )
    st.metric(
              "Température",
              temperature
    )
    st.metric(
              "Timestamp",
              datetime.now().strftime("%H:%M:%S")
    )
    st.metric(
              "Max Documents",
              max_results
    )

# SECTION HISTORIQUE
st.divider()
st.subheader("📝 Historique des interactions")

if "chat_history" in st.session_state and st.session_state.chat_history:
      for i, entry in enumerate(st.session_state.chat_history, 1):
                with st.expander(f"Interaction {i}: {entry['prompt'][:50]}..."):
                              st.write(f"**Prompt:** {entry['prompt']}")
                              st.write(f"**Réponse:** {entry['response']}")
                              st.write(f"**Sources:** {', '.join(entry['sources'])}")
                              st.caption(f"🕐 {entry['timestamp']}")
else:
    st.info("Aucune interaction pour le moment")

# FOOTER
st.divider()
st.caption("NExUS v2.5 | RAG + Gemini 2.0 | Powered by Vertex AI + Streamlit")
