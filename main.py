import functions_framework
from vertexai.generative_models import GenerativeModel
from google.cloud import discoveryengine
import json
import vertexai

PROJECT_ID = "syndicat-novembre-2025"
LOCATION = "europe-west1"
DATA_STORE_ID = "nexus-cgsp-pdf-global_1734540151649"
VIOLATION_KEYWORDS = ["violation", "illegal", "non conforme", "invalide", "ne respecte pas", "contraire", "avis insuffisant", "inferieur"]

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

def search_discovery_engine(query):
    try:
        client = discoveryengine.DocumentServiceClient()
        request = discoveryengine.SearchRequest(
            serving_config=f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATA_STORE_ID}/servingConfigs/default_config",
            query=query,
            page_size=5)
        response = client.search(request)
        results = [r.document.derived_struct_data for r in response.results]
        print(f"[DATA_STORE] Found {len(results)} documents")
        return results
    except Exception as e:
        print(f"[ERROR_DATA_STORE] {str(e)}")
        return []

def check_compliance(question):
    try:
        # Initialize Gemini model
        model = GenerativeModel("gemini-pro")
        
        # Prepare context from data store
        documents = search_discovery_engine(question)
        context = "\n".join([str(doc) for doc in documents]) if documents else "No documents found"
        
        # Create prompt
        prompt = f"""You are a compliance expert for labor rights. Analyze the following question against the context provided and identify any violations.
        
Question: {question}

Context from company documents:
{context}

Respond with JSON format:
{{"compliance": "CONFORME" or "NON-CONFORME", "reason": "explanation", "sources": ["source1", "source2"]}}"""
        
        response = model.generate_content(prompt)
        
        # Parse response
        try:
            result = json.loads(response.text)
            return result
        except:
            return {"compliance": "ERROR", "reason": response.text}
            
    except Exception as e:
        print(f"[ERROR_VERTEX_AI] {str(e)}")
        return {"compliance": "ERROR", "reason": str(e)}

@functions_framework.http
def lech_solidar_orchestrator(request):
    """HTTP Cloud Function entry point"""
    try:
        # Get question from request
        request_json = request.get_json(silent=True) or {}
        question = request_json.get('question') or request.args.get('question')
        
        if not question:
            return {"error": "No question"}, 400
        
        print(f"[INIT] Cloud Function invoked")
        print(f"[QUESTION] {question}")
        
        # Check compliance
        result = check_compliance(question)
        
        return result, 200
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {"error": str(e)}, 500
