"""
NEXUS Plateforme v4.0 - CHU Brugmann
Recherche hybride multi-sources : Discovery Engine (PDF + Web) + BigQuery (CCT)
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
    """
    Extrait titre, contenu et source depuis un resultat Discovery Engine.
    source_label: 'PDF' ou 'WEB' pour distinguer l'origine.
    """
    doc = result.document
    derived = dict(doc.derived_struct_data) if doc.derived_struct_data else {}
    struct = dict(doc.struct_data) if doc.struct_data else {}

    # Titre
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

    # Contenu via extractive_answers (PDFs) ou snippets (web)
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

    content = "\\n\\n".join(content_parts)[:2000]

    # Source URI
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
    """Cree et retourne les credentials GCP depuis le secret Streamlit."""
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
    """
    Interroge un seul Data Store Discovery Engine.
    """
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
    """
    Interroge simultanement PDF + WEB et fusionne les resultats.
    """
    results_pdf = query_discovery_engine_single(query, DATASTORE_PDF, "PDF", credentials)
    results_web = query_discovery_engine_single(query, DATASTORE_WEB, "WEB", credentials)
    return results_pdf + results_web


# ==================== SOURCE B: BIGQUERY (CCT) ====================

def query_bigquery_cct(query: str, credentials) -> List[Dict]:
    """
    Recherche les CCT pertinentes dans BigQuery via une requete SQL avec LIKE.
    Retourne les 5 regles les plus recentes correspondant a la question.
    """
    try:
        client = bigquery.Client(
            project=PROJECT_ID,
            credentials=credentials
        )

        # Mots-cles extraits de la question pour le filtre LIKE
        keywords = [w for w in query.split() if len(w) > 4][:3]

        if not keywords:
            # Pas de mots-cles utiles: retourne les 5 dernieres CCT
            sql = f"""
                SELECT *
                FROM `{BQ_TABLE}`
                ORDER BY COALESCE(date_extraction, date_entree_vigueur, CURRENT_DATE()) DESC
                LIMIT 5
            """
        else:
            # Filtre par mots-cles sur les colonnes textuelles disponibles
            like_clauses = []
            for kw in keywords:
                kw_safe = kw.replace("'", "''")
                like_clauses.append(
                    f"(LOWER(CAST(regle AS STRING)) LIKE LOWER('%{kw_safe}%')"
                    f" OR LOWER(CAST(sujet AS STRING)) LIKE LOWER('%{kw_safe}%')"
                    f" OR LOWER(CAST(source_cct AS STRING)) LIKE LOWER('%{kw_safe}%'))"
                )
            where_clause = " OR ".join(like_clauses)
            sql = f"""
                SELECT *
                FROM `{BQ_TABLE}`
                WHERE {where_clause}
                ORDER BY COALESCE(date_extraction, date_entree_vigueur, CURRENT_DATE()) DESC
                LIMIT 5
            """

        query_job = client.query(sql)
        rows = list(query_job.result())

        if not rows:
            return []

        # Convertit les lignes en dicts exploitables
        documents = []
        for row in rows:
            row_dict = dict(row)
            # Construit un contenu lisible pour Gemini
            content_parts = []
            for col, val in row_dict.items():
                if val is not None and str(val).strip():
                    content_parts.append(f"{col}: {str(val)[:200]}")
            content = "\\n".join(content_parts)

            title = (
                str(row_dict.get("sujet", ""))
                or str(row_dict.get("source_cct", ""))
                or str(row_dict.get("numero_cct", ""))
                or "CCT sans titre"
            )

            documents.append({
                "title": title,
                "content": content,
                "snippet": content[:300],
                "source_uri": str(row_dict.get("source_cct", "") or row_dict.get("lien", "") or "BigQuery"),
                "doc_id": str(row_dict.get("id", "")),
                "source_type": "CCT_BIGQUERY",
            })

        return documents

    except Exception as e:
        err_str = str(e)
        if "Not found" in err_str or "404" in err_str:
            st.warning("⚠️ BigQuery: table CCT introuvable (verifiez le nom)")
        elif "403" in err_str or "denied" in err_str.lower():
            st.warning("⚠️ BigQuery: permission refusee (roles/bigquery.dataViewer requis)")
        else:
            st.warning(f"⚠️ BigQuery CCT erreur: {err_str[:80]}")
        return []


# ==================== GENERATION GEMINI ====================

def build_system_prompt(commission_paritaire: str, region_normes: str) -> str:
    """
    Construit le system prompt dynamique selon le contexte CP et Region choisis.
    """
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
Cette regle s'applique meme si le protocole interne ou la CCT semble plus restrictif que la loi.

SOURCES -- DISTINCTIONS OBLIGATOIRES:
Tu as acces a trois types de sources. Tu DOIS indiquer clairement l'origine de chaque information:
- [SOURCE PDF] : Protocoles internes CHU Brugmann (520 documents indexes)
- [SOURCE WEB] : Veille juridique web (sites officiels, actualites legislatives)
- [SOURCE CCT BigQuery] : Conventions collectives extraites et indexees en base de donnees

INSTRUCTIONS DE REPONSE:
1. Structure ta reponse avec des sections claires
2. Pour chaque affirmation juridique, cite la source entre crochets [SOURCE PDF], [SOURCE WEB] ou [SOURCE CCT BigQuery]
3. Si les sources se contredisent, applique la regle de faveur et explique ton raisonnement
4. Si une information est absente de toutes les sources RAG, indique-le explicitement et base-toi sur ta connaissance du droit belge
5. Termine par une recommandation pratique concrete pour le delegue syndical
6. En cas de doute sur un point complexe, recommande de consulter un juriste specialise en {cp_short}
"""


def generate_response(
    user_input: str,
    rag_pdf_web: List[Dict],
    rag_cct: List[Dict],
    model_choice: str,
    commission_paritaire: str,
    region_normes: str
) -> str:
    """
    Genere une reponse Gemini avec contexte multi-sources (PDF + WEB + CCT BigQuery).
    """
    try:
        system_prompt = build_system_prompt(commission_paritaire, region_normes)

        # Construit le contexte PDF + WEB
        context_pdf_web = ""
        pdf_docs = [d for d in rag_pdf_web if d["source_type"] == "PDF"]
        web_docs = [d for d in rag_pdf_web if d["source_type"] == "WEB"]

        if pdf_docs:
            context_pdf_web += "\\n--- PROTOCOLES CHU BRUGMANN (Discovery Engine PDF) ---\\n"
            for i, doc in enumerate(pdf_docs, 1):
                context_pdf_web += f"\\n[SOURCE PDF {i}] {doc['title']}\\n"
                if doc['content']:
                    context_pdf_web += f"{doc['content']}\\n"
                if doc['source_uri']:
                    context_pdf_web += f"Fichier: {doc['source_uri']}\\n"

        if web_docs:
            context_pdf_web += "\\n--- VEILLE JURIDIQUE WEB (Discovery Engine Web) ---\\n"
            for i, doc in enumerate(web_docs, 1):
                context_pdf_web += f"\\n[SOURCE WEB {i}] {doc['title']}\\n"
                if doc['content']:
                    context_pdf_web += f"{doc['content']}\\n"
                if doc['source_uri']:
                    context_pdf_web += f"URL: {doc['source_uri']}\\n"

        if not pdf_docs and not web_docs:
            context_pdf_web = "\\n[Aucun document PDF ou web pertinent trouve pour cette question]\\n"

        # Construit le contexte CCT BigQuery
        context_cct = ""
        if rag_cct:
            context_cct = "\\n--- CCT EXTRAITES (BigQuery -- Veille Juridique) ---\\n"
            for i, doc in enumerate(rag_cct, 1):
                context_cct += f"\\n[SOURCE CCT BigQuery {i}] {doc['title']}\\n"
                if doc['content']:
                    context_cct += f"{doc['content']}\\n"
        else:
            context_cct = "\\n[Aucune CCT pertinente trouvee dans BigQuery pour cette question]\\n"

        full_prompt = f"""{system_prompt}

========================================
QUESTION DU DELEGUE SYNDICAL:
{user_input}

========================================
{context_pdf_web}

========================================
{context_cct}

========================================
CONSIGNE FINALE:
Reponds en francais. Applique la hierarchie legale belge et la regle de faveur.
Cite chaque source avec son label [SOURCE PDF], [SOURCE WEB] ou [SOURCE CCT BigQuery].
Formule une recommandation pratique en conclusion."""

        model = genai.GenerativeModel(model_choice)
        response = model.generate_content(full_prompt)
        return response.text if response.text else "Gemini n'a pas retourne de reponse."

    except Exception as e:
        return f"❌ Erreur generation reponse: {str(e)[:100]}"


# ==================== MAIN CHAT ====================

st.divider()
col_title, col_context = st.columns([3, 1])
with col_title:
    st.header("💬 Consultation Juridique NExUS")
with col_context:
    cp_badge = commission_paritaire.split(" -- ")[0]
    region_badge = region_normes.split(" (")[0]
    st.markdown(f"**{cp_badge}** | {region_badge}")

st.markdown(
    "Posez votre question. Le systeme interroge simultanement les **520 protocoles PDF**, "
    "la **veille juridique web** et les **CCT en base de donnees**."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources_pdf_web") or message.get("sources_cct"):
            with st.expander("📄 Sources consultees"):
                all_sources = message.get("sources_pdf_web", []) + message.get("sources_cct", [])
                for src in all_sources:
                    icon = {"PDF": "📄", "WEB": "🌐", "CCT_BIGQUERY": "🗄️"}.get(src["source_type"], "📎")
                    label = src["title"] or src["doc_id"] or "Sans titre"
                    uri = src["source_uri"] or ""
                    st.markdown(f"{icon} **[{src['source_type']}]** {label}")
                    if uri:
                        st.caption(f"   {uri}")

# Input utilisateur -- variable nommee user_input partout (pas de user_query)
if user_input := st.chat_input("Posez votre question juridique..."):

    if not all_ok:
        st.error("⚠️ Systeme non configure. Verifiez les diagnostics dans la sidebar.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Recupere credentials une seule fois
    credentials = get_gcp_credentials()
    if not credentials:
        st.error("❌ Impossible de creer les credentials GCP.")
        st.stop()

    # Recherche multi-sources en parallele (sequentielle pour Streamlit)
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.spinner("📄 Protocoles PDF..."):
            pass
    with col2:
        with st.spinner("🌐 Veille web..."):
            pass
    with col3:
        with st.spinner("🗄️ CCT BigQuery..."):
            pass

    with st.spinner("🔍 Recherche multi-sources en cours..."):
        rag_pdf_web = query_all_discovery_engines(user_input, credentials)
        rag_cct = query_bigquery_cct(user_input, credentials)

    count_pdf = sum(1 for d in rag_pdf_web if d["source_type"] == "PDF")
    count_web = sum(1 for d in rag_pdf_web if d["source_type"] == "WEB")
    count_cct = len(rag_cct)

    st.caption(
        f"Sources trouvees: 📄 {count_pdf} PDF | 🌐 {count_web} Web | 🗄️ {count_cct} CCT"
    )

    with st.spinner("⚖️ Gemini analyse et applique la regle de faveur..."):
        response_text = generate_response(
            user_input,
            rag_pdf_web,
            rag_cct,
            model_choice,
            commission_paritaire,
            region_normes
        )

    with st.chat_message("assistant"):
        st.markdown(response_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "sources_pdf_web": rag_pdf_web,
        "sources_cct": rag_cct,
    })

    # Expander detail des sources
    if rag_pdf_web or rag_cct:
        with st.expander(f"📊 Detail des sources ({count_pdf} PDF + {count_web} Web + {count_cct} CCT)"):
            if rag_pdf_web:
                st.subheader("📄 Protocoles & Veille (Discovery Engine)")
                for i, doc in enumerate(rag_pdf_web, 1):
                    icon = "📄" if doc["source_type"] == "PDF" else "🌐"
                    st.markdown(f"**{icon} {i}. {doc['title']}** `[{doc['source_type']}]`")
                    st.caption(f"Source: {doc['source_uri']}")
                    if doc['snippet']:
                        st.markdown(f"> {doc['snippet'][:200]}")
                    st.divider()
            if rag_cct:
                st.subheader("🗄️ CCT (BigQuery)")
                for i, doc in enumerate(rag_cct, 1):
                    st.markdown(f"**🗄️ {i}. {doc['title']}** `[CCT_BIGQUERY]`")
                    st.caption(f"Source: {doc['source_uri']}")
                    if doc['snippet']:
                        st.markdown(f"> {doc['snippet'][:200]}")
                    st.divider()


# ==================== FOOTER ====================
st.divider()
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Messages", len(st.session_state.messages))
with c2:
    st.metric("Streamlit", st.__version__)
with c3:
    st.metric("Sources", "PDF + Web + CCT")
with c4:
    st.metric("Mode", "PLATEFORME v4.0")

st.caption("⚖️ NExUS Plateforme v4.0 -- Production | Hierarchie legale belge + Regle de Faveur")
st.caption("📚 Base documentaire: 520 protocoles CHU Brugmann synchronises | CCT via BigQuery | Veille web active")
