import streamlit as st
import requests
import base64
import json
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="NExUS - LECH Solidar", page_icon="✊", layout="wide")
st.markdown("""
<style>
    h1 { color: #E2001A; }
    h2 { color: #E2001A; }
    .alerte-faveur {
        background-color: #FFCCCC;
        border-left: 5px solid #E2001A;
        padding: 12px;
        margin: 8px 0;
        border-radius: 4px;
    }
    .source-citation {
        background-color: #F0F2F6;
        border-left: 4px solid #4A90D9;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.9em;
        border-radius: 2px;
    }
    .rapport-section {
        background-color: #FAFAFA;
        border: 1px solid #DDD;
        padding: 16px;
        margin: 12px 0;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

cloud_url = st.secrets.get("CLOUD_FUNCTION_URL", "")
project_id = st.secrets.get("PROJECT_ID", "")

# --- Prompt système pour citations et conformité ---
SYSTEM_PROMPT_CITATION = (
    "Tu es NExUS, assistant juridique de la délégation CGSP au CHU Brugmann. "
    "Règles ABSOLUES pour chaque réponse : "
    "1) CITE toujours la source exacte (ex: 'Art. 5, CCT du 12/03/2019 - CP 330', "
    "'Protocole Brugmann du 15/01/2022, Section 3.2', 'Loi du 04/08/1996, Art. 32'). "
    "2) Filtre exclusivement sur les données iris_brugmann pour les protocoles locaux. "
    "3) Applique le PRINCIPE DE FAVEUR : si une disposition est MOINS favorable "
    "qu'une CCT CP 330 ou une loi fédérale, signale-le clairement avec '[ALERTE FAVEUR]'. "
    "4) Structure ta réponse : Analyse > Sources > Recommandation d'action. "
    "5) Région : Bruxelles-Capitale uniquement."
)

SYSTEM_PROMPT_AUDIT = (
    "Tu es NExUS en mode AUDIT DE CONFORMITÉ. "
    "Analyse le document ou la proposition soumise et confronte-le aux normes : "
    "- CCT de la Commission Paritaire 330 (Santé Publique) "
    "- Protocoles internes CHU Brugmann (iris_brugmann) "
    "- Législation fédérale belge (Loi Bien-être, Loi Contrats de Travail, etc.) "
    "Pour CHAQUE point du document : "
    "1) Indique s'il est CONFORME ou NON-CONFORME. "
    "2) Si non-conforme, cite la norme violée (source exacte). "
    "3) Applique le Principe de Faveur : signale avec '[ALERTE FAVEUR]' "
    "toute disposition moins favorable qu'une norme supérieure. "
    "4) Génère des points pour l'ordre du jour CPPT/Conseil d'Entreprise. "
    "5) Filtre iris_brugmann pour les protocoles locaux."
)

# --- Header ---
st.title("✊ NExUS - LECH Solidar")
st.write("Intelligence Juridique & Audit de Conformité pour le CHU Brugmann")

# --- Sidebar ---
st.sidebar.markdown("## ⚙️ Configuration du Profil")
cp = st.sidebar.selectbox("Commission Paritaire", ["CP 330 (Santé Publique)", "Autre CP"])
service = st.sidebar.selectbox("Service", [
    "Soins Infirmiers", "Technique", "Logistique", "Administration", "Direction"
])
statut = st.sidebar.selectbox("Statut de l'Agent", [
    "Statutaire/Nommé", "Contractuel", "Stagiaire", "Étudiant"
])
st.sidebar.markdown("---")
st.sidebar.write("**Région**: Bruxelles-Capitale")
st.sidebar.write("**Data Store**: iris_brugmann")

# --- Métriques ---
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Commission", "CP 330")
c2.metric("Service", service)
c3.metric("Statut", statut)
st.divider()

# --- Helper : appel Cloud Function ---
def appel_nexus(query_text, mode="question"):
    if not cloud_url.startswith("http"):
        st.error("URL de la Cloud Function invalide ou manquante dans les Secrets.")
        return None
    system_prompt = SYSTEM_PROMPT_AUDIT if mode == "audit" else SYSTEM_PROMPT_CITATION
    payload = {
        "query": f"{system_prompt}\n\nQuestion/Document:\n{query_text}",
        "commission_paritaire": cp,
        "service": service,
        "statut": statut,
        "region": "Bruxelles-Capitale",
        "data_store_filter": "iris_brugmann",
        "mode": mode
    }
    try:
        response = requests.post(cloud_url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur serveur: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion: {e}")
        return None

# --- Helper : formater réponse avec alertes ---
def afficher_reponse(data):
    messages = data.get("fulfillmentMessages", [])
    if not messages:
        st.warning("Pas de réponse reçue du moteur.")
        return
    reply = messages[0].get("text", {}).get("text", ["Pas de réponse"])[0]
    # Détection Principe de Faveur
    if "[ALERTE FAVEUR]" in reply:
        parts = reply.split("[ALERTE FAVEUR]")
        st.markdown(parts[0])
        for part in parts[1:]:
            st.markdown(
                f'<div class="alerte-faveur">'
                f'⚠️ <strong>ALERTE PRINCIPE DE FAVEUR</strong><br>{part.strip()}'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info(reply)

# --- Helper : générer rapport d'action ---
def generer_rapport_action(analyse_text):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    rapport = f"""
<div class="rapport-section">
<h4>📋 Rapport d'Action - Généré le {now}</h4>
<p><strong>Points suggérés pour l'Ordre du Jour (CPPT / Conseil d'Entreprise) :</strong></p>
{analyse_text}
<hr>
<p><em>Document généré par NExUS - LECH Solidar | CP 330 | CHU Brugmann</em></p>
</div>
"""
    return rapport


# =====================================================
# ONGLETS PRINCIPAUX
# =====================================================
tab1, tab2, tab3 = st.tabs([
    "🔍 Question Juridique",
    "🛡️ Audit de Conformité",
    "📋 Rapport d'Action"
])

# --- TAB 1 : Question Juridique ---
with tab1:
    st.write("### Posez votre question juridique :")
    question = st.text_area(
        "Votre question",
        placeholder="Exemple: Comment réclamer une prime d'ancienneté si l'employeur refuse?",
        height=100,
        key="q_juridique"
    )
    col_q1, col_q2 = st.columns(2)
    if col_q1.button("🔍 Interroger la Base Juridique", key="btn_question"):
        if question.strip():
            with st.spinner("📚 Interrogation de la base juridique en cours..."):
                data = appel_nexus(question, mode="question")
                if data:
                    afficher_reponse(data)
        else:
            st.warning("Veuillez poser une question.")
    if col_q2.button("🗑️ Effacer", key="btn_clear_q"):
        st.rerun()

# --- TAB 2 : Audit de Conformité ---
with tab2:
    st.write("### 🛡️ Audit de Conformité - Analyse de Documents")
    st.caption(
        "Soumettez une proposition de la direction (texte ou PDF) "
        "pour la confronter aux CCT CP 330, protocoles Brugmann et lois fédérales."
    )

    audit_mode = st.radio(
        "Mode de saisie :",
        ["✍️ Texte libre", "📄 Upload PDF"],
        horizontal=True,
        key="audit_mode"
    )

    audit_text = ""

    if audit_mode == "✍️ Texte libre":
        audit_text = st.text_area(
            "Collez le texte de la proposition :",
            placeholder="Collez ici le texte de la note de service, du règlement ou de la proposition...",
            height=200,
            key="audit_text"
        )
    else:
        uploaded_file = st.file_uploader(
            "Chargez un document PDF :",
            type=["pdf"],
            key="audit_pdf"
        )
        if uploaded_file is not None:
            pdf_bytes = uploaded_file.read()
            pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
            audit_text = (
                f"[DOCUMENT PDF encodé en base64 - "
                f"Nom: {uploaded_file.name}, "
                f"Taille: {len(pdf_bytes)} octets]\n"
                f"Analyse ce document PDF et vérifie sa conformité.\n"
                f"Contenu base64: {pdf_b64[:500]}..."
            )
            st.success(f"✅ Fichier '{uploaded_file.name}' chargé ({len(pdf_bytes):,} octets)")

    if st.button("🛡️ Lancer l'Audit de Conformité", key="btn_audit"):
        if audit_text.strip():
            with st.spinner("🔍 Analyse de conformité en cours (CCT CP 330 + Protocoles Brugmann + Législation)..."):
                data = appel_nexus(audit_text, mode="audit")
                if data:
                    st.write("#### Résultats de l'Audit :")
                    afficher_reponse(data)
                    # Stocker pour génération de rapport
                    messages = data.get("fulfillmentMessages", [])
                    if messages:
                        reply = messages[0].get("text", {}).get("text", [""])[0]
                        st.session_state["dernier_audit"] = reply
        else:
            st.warning("Veuillez saisir un texte ou charger un PDF à auditer.")

# --- TAB 3 : Rapport d'Action ---
with tab3:
    st.write("### 📋 Générateur de Rapport d'Action")
    st.caption(
        "Générez automatiquement des points pour l'ordre du jour "
        "du CPPT ou du Conseil d'Entreprise basés sur les analyses NExUS."
    )

    dernier_audit = st.session_state.get("dernier_audit", "")

    if dernier_audit:
        st.write("**Dernière analyse disponible** (depuis l'onglet Audit) :")
        with st.expander("Voir l'analyse source", expanded=False):
            st.write(dernier_audit)
    else:
        st.info(
            "💡 Lancez d'abord un Audit de Conformité (onglet précédent) "
            "ou saisissez manuellement les points ci-dessous."
        )

    rapport_custom = st.text_area(
        "Points complémentaires pour le rapport :",
        placeholder="Ajoutez ici des observations supplémentaires pour l'ordre du jour...",
        height=100,
        key="rapport_custom"
    )

    organe = st.selectbox(
        "Organe de concertation :",
        ["CPPT (Comité pour la Prévention et la Protection au Travail)",
         "Conseil d'Entreprise",
         "Délégation Syndicale"],
        key="organe"
    )

    if st.button("📋 Générer le Rapport", key="btn_rapport"):
        contenu = dernier_audit if dernier_audit else ""
        if rapport_custom.strip():
            contenu += f"\n\nPoints complémentaires :\n{rapport_custom}"
        if contenu.strip():
            with st.spinner("Rédaction du rapport en cours..."):
                prompt_rapport = (
                    f"Génère un rapport structuré pour l'ordre du jour du {organe}. "
                    f"Base-toi sur l'analyse suivante et formule des points d'action concrets "
                    f"avec références légales (articles, CCT, protocoles). "
                    f"Format : numérotation des points, source juridique pour chacun.\n\n"
                    f"Analyse source :\n{contenu}"
                )
                data = appel_nexus(prompt_rapport, mode="audit")
                if data:
                    messages = data.get("fulfillmentMessages", [])
                    if messages:
                        reply = messages[0].get("text", {}).get("text", [""])[0]
                        rapport_html = generer_rapport_action(reply)
                        st.markdown(rapport_html, unsafe_allow_html=True)
                        st.download_button(
                            label="⬇️ Télécharger le rapport (TXT)",
                            data=f"RAPPORT D'ACTION - {organe}\n"
                                 f"Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                                 f"{'='*60}\n\n{reply}",
                            file_name=f"rapport_nexus_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain"
                        )
        else:
            st.warning("Aucun contenu disponible. Lancez un audit ou saisissez des points.")

# --- Footer ---
st.divider()
st.caption(
    "© 2025 CGSP - Commission Paritaire 330 | Région Bruxelles-Capitale | "
    "Data Store: iris_brugmann | Moteur: NExUS v2.0"
)
