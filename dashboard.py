"""
NEXUS Plateforme v4.0 - CHU Brugmann
Hierarchie legale belge + Regle de Faveur + Contexte CP/Region
"""

import streamlit as st
import google.generativeai as genai
import json
from google.cloud import discoveryengine_v1
from google.cloud import bigquery
from google.oauth2 import service_account
from typing import List, Dict

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="NExUS Plateforme - CHU Brugmann",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ NExUS Plateforme -- CHU Brugmann")
st.markdown("**Expert juridique IA -- Recherche hybride : Protocoles PDF + Veille Web + CCT BigQuery**")

# ==================== CONSTANTES ====================
PROJECT_ID = "syndicat-novembre-2025"
DATASTORE_PDF = "nexus-cgsp-pdf-global"
DATASTORE_WEB = "nexus-websites-cgsp"
BQ_TABLE = f"{PROJECT_ID}.nexus_legal_data.cct_extracted_rules"
DE_LOCATION = "global"

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ CONTEXTE JURIDIQUE")
    st.divider()

    st.subheader("📋 Parametres de la Consultation")
    commission_paritaire = st.selectbox(
        "Commission Paritaire (CP):",
        ["CP 330 -- Sante (CHU Brugmann)", "CP 329 -- Socio-culturel", "Autre / Non specifie"],
        index=0
    )

    region_normes = st.selectbox(
        "Region / Normes applicables:",
        ["Bruxelles-Capitale (IRIS / COCOM)", "Wallonie", "Federal (national)"],
        index=0
    )

    st.divider()
    st.subheader("🔧 DIAGNOSTIC SYSTEME")
    api_key_ok = False
    gcp_json_ok = False
    gemini_ok = False
    discovery_ok = False
    bigquery_ok = False

    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if api_key:
            st.success(f"✅ API KEY OK")
            api_key_ok = True
    except: pass

    try:
        gcp_json_str = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
        if gcp_json_str:
            json.loads(gcp_json_str)
            st.success("✅ GCP JSON OK")
            gcp_json_ok = True
            discovery_ok = True
            bigquery_ok = True
    except: pass

    if api_key_ok:
        try:
            genai.configure(api_key=api_key)
            st.success(f"✅ Gemini OK")
            gemini_ok = True
        except: pass

    all_ok = api_key_ok and gcp_json_ok and gemini_ok
    if all_ok:
        st.success("### 🟢 TOUS SYSTEMES OK")
    else:
        st.warning("### 🟡 VERIFIER CONFIG")

# ==================== HELPERS ====================
def get_gcp_credentials():
    gcp_json_str = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
    if not gcp_json_str: return None
    return service_account.Credentials.from_service_account_info(json.loads(gcp_json_str))

def extract_document_data(result, source_label: str) -> Dict:
    doc = result.document
    derived = dict(doc.derived_struct_data) if doc.derived_struct_data else {}
    struct = dict(doc.struct_data) if doc.struct_data else {}
    
    title = struct.get("title") or derived.get("title") or doc.id or "Sans titre"
    content = ""
    extractive_answers = derived.get("extractive_answers", [])
    if extractive_answers:
        content = "\n".join([a.get("content", "") for a in extractive_answers])
    if not content:
        snippets = derived.get("snippets", [])
        content = "\n".join([s.get("snippet", "") for s in snippets])
    
    return {
        "title": title,
        "content": content[:2000],
        "source_type": source_label
    }

# ==================== RECHERCHE AGRESSIVE BIGQUERY ====================
def query_bigquery_cct(query: str, credentials) -> List[Dict]:
    try:
        client = bigquery.Client(project=PROJECT_ID, credentials=credentials)
        SYNONYMES = {
            "prime": ["prime", "indemnite", "allocation", "supplement"],
            "nuit": ["nuit", "nocturne", "nocturnite"],
            "week-end": ["week-end", "samedi", "dimanche", "dominical"],
            "salaire": ["salaire", "remuneration", "bareme"]
        }
        raw_words = [w.strip('.,;:?!"\'()').lower() for w in query.split() if len(w) > 2]
        keywords_set = set(raw_words)
        for word in raw_words:
            for base, syns in SYNONYMES.items():
                if word in syns or word == base: keywords_set.update(syns)
        
        keywords = list(keywords_set)[:10]
        if not keywords: where_clause = "1=1"
        else:
            clauses = [f"LOWER(raw_text_snippet) LIKE '%{kw.replace(\"'\", \"''\")}%'" for kw in keywords]
            clauses += [f"LOWER(rule_key) LIKE '%{kw.replace(\"'\", \"''\")}%'" for kw in keywords]
            where_clause = " OR ".join(clauses)

        sql = f"SELECT * FROM `{BQ_TABLE}` WHERE {where_clause} ORDER BY effective_date DESC LIMIT 8"
        query_job = client.query(sql)
        documents = []
        for row in query_job.result():
            row_dict = dict(row)
            content = " | ".join([f"{k.upper()}: {v}" for k, v in row_dict.items() if v])
            documents.append({
                "title": str(row_dict.get("rule_key") or "CCT Detail"),
                "content": content,
                "source_type": "CCT_BIGQUERY"
            })
        return documents
    except Exception as e:
        st.warning(f"⚠️ BigQuery Trace: {str(e)[:60]}")
        return []

# ==================== DISCOVERY ENGINE ====================
def query_discovery_engine_single(query, datastore_id, source_label, credentials):
    try:
        client = discoveryengine_v1.SearchServiceClient(credentials=credentials)
        serving_config = f"projects/{PROJECT_ID}/locations/{DE_LOCATION}/collections/default_collection/dataStores/{datastore_id}/servingConfigs/default_search"
        request = discoveryengine_v1.SearchRequest(serving_config=serving_config, query=query, page_size=3)
        response = client.search(request)
        return [extract_document_data(r, source_label) for r in response.results]
    except: return []

# ==================== GENERATION ====================
def generate_response(user_input, rag_pdf_web, rag_cct, model_choice, cp, region):
    model = genai.GenerativeModel(model_choice)
    context = "SOURCES PDF:\n" + "\n".join([d['content'] for d in rag_pdf_web if d['source_type'] == "PDF"])
    context += "\nSOURCES CCT:\n" + "\n".join([d['content'] for d in rag_cct])
    
    prompt = f"Expert juridique CHU Brugmann. CP: {cp}, Region: {region}. Question: {user_input}\n\nContexte:\n{context}\n\nApplique la hierarchie des normes et la regle de faveur."
    response = model.generate_content(prompt)
    return response.text

# ==================== INTERFACE CHAT ====================
if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if user_input := st.chat_input("Votre question..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)
    
    credentials = get_gcp_credentials()
    with st.spinner("Recherche..."):
        r_pdf_web = query_discovery_engine_single(user_input, DATASTORE_PDF, "PDF", credentials)
        r_pdf_web += query_discovery_engine_single(user_input, DATASTORE_WEB, "WEB", credentials)
        r_cct = query_bigquery_cct(user_input, credentials)
    
    with st.spinner("Analyse..."):
        resp = generate_response(user_input, r_pdf_web, r_cct, "gemini-1.5-flash", commission_paritaire, region_normes)
    
    with st.chat_message("assistant"): st.markdown(resp)
    st.session_state.messages.append({"role": "assistant", "content": resp})

st.divider()
st.caption("⚖️ NExUS Plateforme v4.0")
