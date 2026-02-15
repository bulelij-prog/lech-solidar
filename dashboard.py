import streamlit as st
import json
import google.auth
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from vertexai.generative_models import GenerativeModel
import vertexai

# ============================================================
# INITIALISATION DU CLIENT VERTEX AI AVEC SERVICE ACCOUNT
# ============================================================

def initialize_vertex_ai():
    """
    Initialise Vertex AI en utilisant les credentials du Service Account
    stockées dans les secrets Streamlit.
    """
    # Récupère le JSON du service account depuis les secrets
    service_account_json = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
    
    if not service_account_json:
        st.error("❌ Le secret GCP_SERVICE_ACCOUNT_JSON n'est pas configuré dans Streamlit Secrets")
        st.stop()
    
    # Crée les credentials à partir du JSON
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(service_account_json)
    )
    
    # Récupère le project ID depuis le JSON
    project_id = json.loads(service_account_json).get("project_id")
    
    if not project_id:
        st.error("❌ Impossible de récupérer le project_id du service account")
        st.stop()
    
    # Initialise Vertex AI avec le project et les credentials
    vertexai.init(project=project_id, credentials=credentials)
    
    return project_id, credentials

# Initialise Vertex AI au démarrage
if "vertex_ai_initialized" not in st.session_state:
    project_id, credentials = initialize_vertex_ai()
    st.session_state.vertex_ai_initialized = True
    st.session_state.project_id = project_id
    st.session_state.credentials = credentials


# ============================================================
# FONCTION POUR APPELER L'API GEMINI
# ============================================================

def call_gemini_api(prompt: str, model_name: str = "gemini-2.0-flash") -> str:
    """
    Appelle l'API Gemini via Vertex AI en utilisant le Service Account.
    
    Args:
        prompt (str): Le prompt à envoyer à Gemini
        model_name (str): Le modèle à utiliser (défaut: gemini-2.0-flash)
    
    Returns:
        str: La réponse du modèle
    """
    try:
        # Crée une instance du modèle Gemini
        model = GenerativeModel(model_name=model_name)
        
        # Appelle le modèle avec les credentials du service account
        response = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.7,
            }
        )
        
        return response.text
    
    except Exception as e:
        st.error(f"❌ Erreur lors de l'appel à Gemini: {str(e)}")
        return None


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    st.title("NExUS v2.5 - Dashboard avec Vertex AI")
    
    # Exemple simple
    prompt = st.text_area("Entrez votre prompt:", "Bonjour, comment ça marche?")
    
    if st.button("Envoyer à Gemini"):
        response = call_gemini_api(prompt)
        if response:
            st.success("✓ Réponse reçue")
            st.write(response)
```

---

## Ce que ce code fait :

1. **`initialize_vertex_ai()`** : 
   - Récupère le JSON du service account depuis `st.secrets["GCP_SERVICE_ACCOUNT_JSON"]`
   - Crée les credentials authentifiés
   - Initialise Vertex AI avec le project_id et les credentials
   - Retourne le project_id pour référence

2. **Initialisation au démarrage** :
   - Utilise `st.session_state` pour initialiser Vertex AI une seule fois (pour les performances)

3. **`call_gemini_api(prompt)`** :
   - Crée une instance de `GenerativeModel`
   - Appelle le modèle Gemini
   - Retourne la réponse ou une erreur

---

## ⚠️ Points importants :

**Avant de lancer l'app :**

1. **Ajoute le secret dans Streamlit Cloud** :
   - Va dans : Paramètres de l'app → Secrets
   - Ajoute une variable nommée : `GCP_SERVICE_ACCOUNT_JSON`
   - Colle **tout le contenu JSON** du fichier `syndicat-novembre-2025-be7179c9846b.json` que tu as téléchargé

2. **Assure-toi que les packages sont installés** dans `requirements.txt` :
```
   google-auth==2.26.0
   google-auth-oauthlib==1.2.0
   google-cloud-aiplatform==1.42.0
   google-cloud-vertexai==1.42.0
   streamlit==1.28.0
