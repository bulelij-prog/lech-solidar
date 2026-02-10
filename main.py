import functions_framework
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Content
from google.cloud import discoveryengine
import json
import streamlit as st

PROJECT_ID = "syndicat-novembre-2025"
LOCATION = "europe-west1"
DATA_STORE_ID = "nexus-cgsp-pdf-global_1734540151649"
VIOLATION_KEYWORDS = ["violation", "illegal", "non conforme", "invalide", "ne respecte pas", "contraire", "avis insuffisant"]

@st.cache_resource
def init_vertexai():
    """Initialize Vertex AI with caching"""
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    return GenerativeModel("gemini-1.5-pro")

def search_discovery_engine(query):
    """Search using Discovery Engine API"""
    client = discoveryengine.DocumentServiceClient()
    request = discoveryengine.SearchRequest(
        query=query,
        page_size=5)
    response = client.search(request)
    results = [r.document.derived_struct_data for r in response.results]
    print(f"[DATA_STORE] Found {len(results)} documents")
    return results

def check_compliance(question):
    """Main compliance check function"""
    model = init_vertexai()
    prompt = f"""Tu es NExUS, assistant juridique et audit de conformit pour le CHU Brugmann.

SYSTME_PROMPT_CITATION = (
  "Tu es NExUS, assistante juridique de la dlgation CGSP au CHU Brugmann. "
  "Rgles ABSOLUES pour chaque rponse : "
  "1) CITE toujours la source exacte (ex: 'Art. 5, CCT du 12/03/2019 - CP 330', "
  "2) Protocole Brugmann du 15/01/2022, Section 3.2', 'Loi du 04/08/2015...')."
  "3) Applique le PRINCIPE DE FAVEUR : si une disposition est MOINS favorable "
  "qu'une autre, signale-le clairement avec '[ALERTE FAVEUR]'."
  "4) Structure ta rponse : Analyse > Sources > Recommandation d'action. "
  "5) Ds que tu identifies une question hors compliance, signale : '5) Appelle le PRINCIPE DE FAVEUR : si une disposition est MOINS favorable "
  "qu'une autre, signale-le clairement avec '[ALERTE FAVEUR]'."
  "6) Structure ta rponse : Analyse > Sources > Recommandation d'action. "
  "7) Si tu ne sais pas, tu dis : '5) Appelle le PRINCIPE DE FAVEUR : si une disposition est MOINS favorable "
  "qu'une autre, signale-le clairement avec '[ALERTE FAVEUR]'."
  "8) Structure ta rponse : Analyse > Sources > Recommandation d'action. "
  "9) Si tu ne sais pas, tu dis : 'aucun contenu disponible. Lancez un audit ou saisissez des points.'"
)

Question pose: {question}

Utilise UNIQUEMENT les donnes du CHU Brugmann et la jurisprudence belge. Analyse la conformit."""

    response = model.generate_content(prompt)
    
    try:
        result = json.loads(response.text)
        return result
    except:
        return {"compliance": "ERROR", "reason": response.text}

@functions_framework.http
def lech_solidar_orchestrator(request):
    """Cloud Function entry point"""
    print("[INIT] Cloud Function invoked")
    print(f"[QUESTION] {request.args.get('question')}")
    
    # Check compliance
    result = check_compliance(request.args.get('question'))
    
    return result, 200

except Exception as e:
    print(f"[ERROR] {str(e)}")
    return {"error": str(e)}, 500

