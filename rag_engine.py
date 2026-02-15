"""
RAG Engine - Recherche sémantique dans Vertex AI Discovery Engine
Interroge le Data Store 'protocoles-cgsp-datastore-v4' et retourne les documents pertinents
"""

import logging
from typing import Optional, List, Dict, Tuple
from google.cloud import discoveryengine_v1
from google.cloud.discoveryengine_v1.services.search_service import SearchServiceClient
from google.api_core.gapic_v1 import client_info as grpc_client_info

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================================================
# CONFIGURATION DISCOVERY ENGINE
# ================================================================

PROJECT_ID = "syndicat-novembre-2025"
LOCATION = "global"
DATA_STORE_ID = "nexus-cgsp-pdf-global"
SEARCH_ENGINE_ID = "nexus-chat-global"

# Métadonnées du filtrage
HOSPITAL_FILTER = "iris_brugmann"


# ================================================================
# CLASSE PRINCIPALE RAG
# ================================================================

class RAGEngine:
      """Moteur RAG utilisant Vertex AI Discovery Engine"""

    def __init__(self, project_id: str = PROJECT_ID, location: str = LOCATION):
              """
                      Initialise le client Discovery Engine

                                      Args:
                                                  project_id: ID du projet GCP
                                                              location: Localisation (global, eu, etc.)
                                                                      """
              self.project_id = project_id
              self.location = location
              self.client = SearchServiceClient()
              logger.info(f"✓ RAG Engine initialisé - Projet: {project_id}")

    def search_datastore(
              self,
              query: str,
              doc_type_filter: Optional[str] = None,
              max_results: int = 5,
    ) -> Tuple[List[Dict], str]:
              """
                      Recherche sémantique dans le Data Store

                                      Args:
                                                  query: La question/requête de l'utilisateur
                                                              doc_type_filter: Filtre optionnel (Loi, CCT, Protocole)
                                                                          max_results: Nombre max de documents à retourner

                                                                                              Returns:
                                                                                                          Tuple[List[Dict], str]: (liste de documents, contexte formaté pour Gemini)
                                                                                                                  """
              try:
                            # Construction du chemin de la ressource
                            search_config = f"projects/{self.project_id}/locations/{self.location}/collections/default_collection/dataStores/{DATA_STORE_ID}"

            # Paramètres de filtrage
                  filter_str = f'hospital_id = "{HOSPITAL_FILTER}"'
            if doc_type_filter:
                              filter_str += f' AND doc_type = "{doc_type_filter}"'

            # Configuration de la requête
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

            # Exécution de la recherche
            response = self.client.search(request)

            # Extraction des résultats
            documents = []
            context_parts = []

            for result in response.results:
                              doc_data = self._extract_document(result)
                              if doc_data:
                                                    documents.append(doc_data)
                                                    context_parts.append(self._format_context(doc_data))

                          # Formatage du contexte pour Gemini
                          context = self._build_context(documents, context_parts)

            logger.info(f"✓ Recherche réussie: {len(documents)} documents trouvés")
            return documents, context

except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche: {str(e)}")
            return [], ""

    def _extract_document(self, result) -> Optional[Dict]:
              """
                      Extrait les informations pertinentes du résultat

                                      Args:
                                                  result: Objet résultat de la recherche

                                                                      Returns:
                                                                                  Dict avec les données du document ou None
                                                                                          """
        try:
                      doc = result.document

            # Récupération du JSON des métadonnées
                      struct_data = doc.struct_data if hasattr(doc, 'struct_data') else {}

            # Extraction des champs clés
                      filename = struct_data.get('file_name', 'Sans titre')
                      url = doc.uri if hasattr(doc, 'uri') else ""
                      snippet = result.snippet.snippet_status if hasattr(result, 'snippet') else ""

            return {
                              'filename': filename,
                              'url': url,
                              'snippet': snippet,
                              'relevance_score': result.relevance_score if hasattr(result, 'relevance_score') else 0.0,
                              'document_id': doc.id if hasattr(doc, 'id') else "",
            }
except Exception as e:
            logger.warning(f"⚠️  Erreur extraction document: {str(e)}")
            return None

    def _format_context(self, doc_data: Dict) -> str:
              """
                      Formate un document pour le contexte RAG

                                      Args:
                                                  doc_data: Dictionnaire du document

                                                                      Returns:
                                                                                  String formaté pour Gemini
                                                                                          """
        return f"""
        📄 **Source**: {doc_data['filename']}
        📊 **Pertinence**: {doc_data['relevance_score']:.1%}
        📌 **Contenu**: {doc_data['snippet'][:300]}...
        """

    def _build_context(self, documents: List[Dict], context_parts: List[str]) -> str:
              """
                      Construit le contexte complet pour Gemini

                                      Args:
                                                  documents: Liste des documents trouvés
                                                              context_parts: Parties formatées des documents

                                                                                  Returns:
                                                                                              String: Contexte complet
                                                                                                      """
        if not documents:
                      return ""

        context = "## 📚 CONTEXTE - Documents CHU Brugmann\n\n"
        context += "---\n"
        context += "\n".join(context_parts)
        context += "\n---\n"

        return context

    def get_sources_list(self, documents: List[Dict]) -> List[str]:
              """
                      Retourne la liste des noms de fichiers pour affichage

                                      Args:
                                                  documents: Liste des documents

                                                                      Returns:
                                                                                  List[str]: Noms des fichiers
                                                                                          """
        return [doc['filename'] for doc in documents]


# ================================================================
# FONCTION UTILITAIRE POUR STREAMLIT
# ================================================================

def initialize_rag_engine() -> RAGEngine:
      """
          Initialise le moteur RAG (fonction cached pour Streamlit)

                  Returns:
                          RAGEngine: Instance du moteur RAG
                              """
    return RAGEngine(project_id=PROJECT_ID, location=LOCATION)
