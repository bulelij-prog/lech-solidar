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

    # --- Selecteurs de contexte ---
    st.subheader("📋 Parametres de la Consultation")
    commission_paritaire = st.selectbox(
        "Commission Paritaire (CP):",
        [
            "CP 330 -- Sante (CHU Brugmann)",
            "CP 329 -- Socio-culturel",
            "Autre / Non specifie",
        ],
        index=0
    )
    region_normes = st.selectbox(
        "Region / Normes applicables:",
        [
            "Bruxelles-Capitale (IRIS / COCOM)",
            "Wallonie",
            "Federal (national)",
        ],
        index=0
    )

    st.divider()

    # --- Diagnostic ---
    st.subheader("🔧 DIAGNOSTIC SYSTEME")
    api_key_ok = False
    gcp_json_ok = False
    gemini_ok = False
    discovery_ok = False
    bigquery_ok = False

    # Check 1: Secrets
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
        if api_key:
            st.success(f"✅ GOOGLE_API_KEY ({len(api_key)} chars)")
            api_key_ok = True
        else:
            st.error("❌ GOOGLE_API_KEY manquante")
    except Exception as e:
        st.error(f"❌ GOOGLE_API_KEY: {str(e)[:40]}")

    try:
        gcp_json_str = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
        if gcp_json_str:
            try:
                json.loads(gcp_json_str)
                st.success("✅ GCP_SERVICE_ACCOUNT_JSON (JSON valide)")
                gcp_json_ok = True
            except json.JSONDecodeError:
                st.error("❌ GCP JSON: format invalide")
        else:
            st.error("❌ GCP_SERVICE_ACCOUNT_JSON manquant")
    except Exception as e:
        st.error(f"❌ GCP JSON: {str(e)[:40]}")

    # Check 2: Gemini
    try:
        if api_key_ok:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            count = sum(1 for m in models if "generateContent" in m.supported_generation_methods)
            st.success(f"✅ Gemini API ({count} modeles)")
            gemini_ok = True
        else:
            st.error("❌ Gemini: cle API manquante")
    except Exception as e:
        st.error(f"❌ Gemini: {str(e)[:50]}")

    # Check 3: GCP Credentials
    try:
        if gcp_json_ok:
            gcp_json_check = json.loads(st.secrets.get("GCP_SERVICE_ACCOUNT_JSON"))
            service_account.Credentials.from_service_account_info(gcp_json_check)
            st.success("✅ GCP Credentials valides")
            discovery_ok = True
            bigquery_ok = True
        else:
            st.error("❌ GCP Credentials: JSON manquant")
    except Exception as e:
        st.error(f"❌ GCP Credentials: {str(e)[:60]}")

    st.divider()

    # --- Model selector ---
    st.subheader("📌 Modele Gemini")
    if gemini_ok:
        model_choice = st.selectbox(
            "Modele:",
            ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
            index=0
        )
    else:
        st.warning("Modele indisponible (connexion echouee)")
        model_choice = "gemini-2.0-flash"

    st.divider()

    # --- Status global ---
    all_ok = api_key_ok and gcp_json_ok and gemini_ok and discovery_ok
    if all_ok:
        st.success("### 🟢 TOUS SYSTEMES OK")
    else:
        st.warning("### 🟡 VERIFIER LES ERREURS CI-DESSUS")

    st.divider()
    st.caption(f"CP: {commission_paritaire.split(' -- ')[0]}")
    st.caption(f"Region: {region_normes.split(' (')[0]}")


# ==================== HELPERS: Extraction document ====================
def extract_document_data(result, source_label: str) -> Dict:
    doc = result.document
    derived = dict(doc.derived_struct_data) if doc.derived_struct_data else {}
    struct = dict(doc.struct_data) if doc.struct_data else {}

    title = (
        struct.get("title")
        or struct.get("name")
        or derived.get("title")
        or derived.get("name")
        or derived.get("link", "").split("/")[-1]
        or doc.name.split("/")[-1]
        or doc.id
        or "Document sans titre"
    )

    content_parts = []
    extractive_answers = derived.get("extractive_answers", [])
    if extractive_answers:
        for answer in extractive_answers:
            if isinstance(answer, dict):
                page_num = answer.get("pageNumber", "")
                text = answer.get("content", "").strip()
                if text:
                    prefix = f"[Page {page_num}] " if page_num else ""
                    content_parts.append(f"{prefix}{text}")

    if not content_parts:
        snippets = derived.get("snippets", [])
        for snippet in snippets:
            if isinstance(snippet, dict):
                text = snippet.get("snippet", "").strip()
                if text:
                    content_parts.append(text)

    if not content_parts:
        fallback = (
            derived.get("content", "")
            or struct.get("content", "")
            or struct.get("text", "")
            or struct.get("body", "")
        )
        if fallback:
            content_parts.append(fallback)

    content = "\n\n".join(content_parts)[:2000]

    source_uri = (
        struct.get("source_uri", "")
        or struct.get("uri", "")
        or derived.get("link", "")
        or derived.get("source_uri", "")
        or doc.name
    )

    return {
        "title": title,
        "content": content,
        "snippet": content[:300],
        "source_uri": source_uri,
        "doc_id": doc.id or "",
        "source_type": source_label,
    }


def get_gcp_credentials():
    gcp_json_str = st.secrets.get("GCP_SERVICE_ACCOUNT_JSON")
    if not gcp_json_str:
        return None
    try:
        gcp_json = json.loads(gcp_json_str)
        return service_account.Credentials.from_service_account_info(gcp_json)
    except Exception:
        return None


# ==================== SOURCE A: DISCOVERY ENGINE (PDF + WEB) ====================
def query_discovery_engine_single(
    query: str,
    datastore_id: str,
    source_label: str,
    credentials
) -> List[Dict]:
    try:
        client = discoveryengine_v1.SearchServiceClient(credentials=credentials)
        serving_config = (
            f"projects/{PROJECT_ID}"
            f"/locations/{DE_LOCATION}"
            f"/collections/default_collection"
            f"/dataStores/{datastore_id}"
            f"/servingConfigs/default_search"
        )
        request = discoveryengine_v1.SearchRequest(
            serving_config=serving_config,
            query=query,
            page_size=3,
        )
        response = client.search(request)
        documents = []
        for result in response.results:
            try:
                doc_data = extract_document_data(result, source_label)
                documents.append(doc_data)
            except Exception:
                continue
        return documents
    except Exception as e:
        st.warning(f"⚠️ Discovery Engine [{source_label}] erreur: {str(e)[:80]}")
        return []


def query_all_discovery_engines(query: str, credentials) -> List[Dict]:
    results_pdf = query_discovery_engine_single(query, DATASTORE_PDF, "PDF", credentials)
    results_web = query_discovery_engine_single(query, DATASTORE_WEB, "WEB", credentials)
    return results_pdf + results_web


# ==================== SOURCE B: BIGQUERY (CCT) ====================
def query_bigquery_cct(query: str, credentials) -> List[Dict]:
    try:
        client = bigquery.Client(
            project=PROJECT_ID,
            credentials=credentials
        )

        SYNONYMES = {
            "prime":      ["prime", "primes", "indemnite", "indemnites", "allocation", "supplement"],
            "nuit":       ["nuit", "nocturne", "nocturnite", "nuits"],
            "week-end":   ["week-end", "weekend", "samedi", "dimanche"],
            "conge":      ["conge", "conges", "vacances", "repos"],
            "salaire":    ["salaire", "remuneration", "traitement", "bareme"],
            "maladie":    ["maladie", "incapacite", "absence", "arret"],
            "heures":     ["heures", "heure", "horaire", "duree", "temps"],
            "supplementaires": ["supplementaires", "surtemps", "heures-sup", "overtime"],
            "anciennete": ["anciennete", "baremo", "echelon"],
            "preambule":  ["preambule", "objet", "champ"],
            "syndicat":   ["syndicat", "delegation", "delegue", "organisation"],
        }

        # Extraction des mots bruts de la question (FIX syntaxe guillemets)
        raw_words = [
            w.strip('.,;:?!"\'()').lower() 
            for w in query.split() 
            if len(w.strip('.,;:?!"\'()')) > 2
        ]

        keywords_set = set()
        for word in raw_words:
            keywords_set.add(word)
            for base, synonyms in SYNONYMES.items():
                if word in synonyms or word == base:
                    keywords_set.update(synonyms)

        keywords = list(keywords_set)[:10]

        if not keywords:
            sql = f"""
                SELECT *
                FROM `{BQ_TABLE}`
                ORDER BY COALESCE(effective_date, CURRENT_DATE()) DESC
                LIMIT 5
            """
        else:
            like_clauses = []
            for kw in keywords:
                kw_safe = kw.replace("'", "''")
                clause = (
                    "(LOWER(COALESCE(rule_key, '')) LIKE LOWER('%" + kw_safe + "%')"
                    " OR LOWER(COALESCE(raw_text_snippet, '')) LIKE LOWER('%" + kw_safe + "%')"
                    " OR LOWER(COALESCE(rule_category, '')) LIKE LOWER('%" + kw_safe + "%'))"
                )
                like_clauses.append(clause)

            where_clause = " OR ".join(like_clauses)
            sql = f"""
                SELECT *
                FROM `{BQ_TABLE}`
                WHERE {where_clause}
                ORDER BY COALESCE(effective_date, CURRENT_DATE()) DESC
                LIMIT 5
            """

        query_job = client.query(sql)
        rows = list(query_job.result())

        if not rows:
            return []

        documents = []
        for row in rows:
            row_dict = dict(row)
            content_parts = []
            for col, val in row_dict.items():
                if val is not None and str(val).strip():
                    content_parts.append(f"{col}: {str(val)[:200]}")
            content = "\n".join(content_parts)

            title = (
                str(row_dict.get("rule_category") or "")
                or str(row_dict.get("document_source_uri") or "")
                or str(row_dict.get("rule_key") or "")
                or "CCT sans titre"
            )

            documents.append({
                "title": title,
                "content": content,
                "snippet": content[:300],
                "source_uri": str(row_dict.get("document_source_uri", "") or row_dict.get("lien", "") or "BigQuery"),
                "doc_id": str(row_dict.get("id", "")),
                "source_type": "CCT_BIGQUERY",
            })
        return documents

    except Exception as e:
        err_str = str(e)
        if "Not found" in err_str or "404" in err_str:
            st.warning("⚠️ BigQuery: table CCT introuvable")
        else:
            st.warning(f"⚠️ BigQuery CCT erreur: {err_str[:80]}")
        return []


# ==================== GENERATION GEMINI ====================
def build_system_prompt(commission_paritaire: str, region_normes: str) -> str:
    cp_short = commission_paritaire.split(" -- ")[0]
    region_short = region_normes.split(" (")[0]

    return f"""Tu es un expert juridique specialise en droit du travail belge, mandate par les delegues syndicaux du CHU Brugmann.

CONTEXTE DE LA CONSULTATION:
- Commission Paritaire: {commission_paritaire}
- Cadre territorial: {region_short}
- Etablissement: CHU Brugmann (Hopital Public -- Bruxelles)

HIERARCHIE LEGALE BELGE (Applique STRICTEMENT dans cet ordre):
1. Loi belge federale (code du travail, loi sur les contrats de travail)
2. Conventions collectives du travail (CCT) -- niveau {cp_short} et niveau entreprise
3. Reglementations regionales {region_short} applicables
4. Protocoles internes du CHU Brugmann

REGLE DE FAVEUR (Principe absolu):
En cas de conflit entre deux normes, applique TOUJOURS celle qui est la plus favorable au travailleur.

SOURCES -- DISTINCTIONS OBLIGATOIRES:
- [SOURCE PDF] : Protocoles internes CHU Brugmann
- [SOURCE WEB] : Veille juridique web
- [SOURCE CCT BigQuery] : Conventions collectives extraites

INSTRUCTIONS DE REPONSE:
1. Cite chaque source entre crochets [SOURCE PDF], [SOURCE WEB] ou [SOURCE CCT BigQuery]
2. Formule une recommandation pratique en conclusion.
"""


def generate_response(
    user_input: str,
    rag_pdf_web: List[Dict],
    rag_cct: List[Dict],
    model_choice: str,
    commission_paritaire: str,
    region_normes: str
) -> str:
    try:
        system_prompt = build_system_prompt(commission_paritaire, region_normes)
        context_pdf_web = ""
        pdf_docs = [d for d in rag_pdf_web if d["source_type"] == "PDF"]
        web_docs = [d for d in rag_pdf_web if d["source_type"] == "WEB"]

        if pdf_docs:
            context_pdf_web += "\n--- PROTOCOLES PDF ---\n"
            for i, doc in enumerate(pdf_docs, 1):
                context_pdf_web += f"\n[SOURCE PDF {i}] {doc['title']}\n{doc['content']}\n"

        if web_docs:
            context_pdf_web += "\n--- VEILLE WEB ---\n"
            for i, doc in enumerate(web_docs, 1):
                context_pdf_web += f"\n[SOURCE WEB {i}] {doc['title']}\n{doc['content']}\n"

        context_cct = ""
        if rag_cct:
            context_cct = "\n--- CCT BIGQUERY ---\n"
            for i, doc in enumerate(rag_cct, 1):
                context_cct += f"\n[SOURCE CCT BigQuery {i}] {doc['title']}\n{doc['content']}\n"

        full_prompt = f"{system_prompt}\n\nQUESTION: {user_input}\n\nCONTEXTE:\n{context_pdf_web}\n{context_cct}"
        
        model = genai.GenerativeModel(model_choice)
        response = model.generate_content(full_prompt)
        return response.text if response.text else "Pas de reponse."

    except Exception as e:
        return f"❌ Erreur: {str(e)[:100]}"


# ==================== MAIN CHAT ====================
st.divider()
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Posez votre question juridique..."):
    if not all_ok:
        st.error("Systeme non configure.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    credentials = get_gcp_credentials()
    with st.spinner("Recherche..."):
        rag_pdf_web = query_all_discovery_engines(user_input, credentials)
        rag_cct = query_bigquery_cct(user_input, credentials)

    with st.spinner("Analyse..."):
        response_text = generate_response(
            user_input, rag_pdf_web, rag_cct, model_choice, commission_paritaire, region_normes
        )

    with st.chat_message("assistant"):
        st.markdown(response_text)
        
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "sources_pdf_web": rag_pdf_web,
        "sources_cct": rag_cct,
    })

# ==================== FOOTER ====================
st.divider()
st.caption("⚖️ NExUS Plateforme v4.0 | 520 protocoles | CCT BigQuery")
