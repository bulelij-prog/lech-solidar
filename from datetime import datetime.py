import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="LECH Solidar", layout="centered")

# ✅ CONFIGURATION SÉCURISÉE - Utilise les Secrets Streamlit
CLOUD_FUNCTION_URL = st.secrets.get("CLOUD_FUNCTION_URL", os.getenv("CLOUD_FUNCTION_URL"))

st.markdown("# ✊ **LECH Solidar**")
st.markdown("*Assistant IA pour les délégués syndicaux du CHU Brugmann*")
st.markdown("---")

# Formulaire de question
with st.form("question_form"):
    question = st.text_input(
            "Posez votre question aux protocoles syndicaux :",
                    placeholder="Ex: Un stagiaire a-t-il droit à la prime de fin d'année ?"
                        )
                            submitted = st.form_submit_button("🔍 Rechercher", use_container_width=True)

                            if submitted and question:
                                st.info("⏳ Recherche en cours dans les protocoles...")
                                    
                                        try:
                                                # Appel à la Cloud Function
                                                        response = requests.post(
                                                                    CLOUD_FUNCTION_URL,
                                                                                json={"question": question},
                                                                                            timeout=60
                                                                                                    )
                                                                                                            
                                                                                                                    if response.status_code == 200:
                                                                                                                                data = response.json()
                                                                                                                                            
                                                                                                                                                        # Affichage de la réponse
                                                                                                                                                                    st.success("✅ Réponse trouvée")
                                                                                                                                                                                
                                                                                                                                                                                            if "fulfillment" in data:
                                                                                                                                                                                                            st.markdown(data["fulfillment"]["messages"][0]["text"])
                                                                                                                                                                                                                        
                                                                                                                                                                                                                                    # Indicateur de conformité
                                                                                                                                                                                                                                                if "compliance_score" in data:
                                                                                                                                                                                                                                                                if data["compliance_score"] == "VERT":
                                                                                                                                                                                                                                                                                    st.markdown("#### 🟢 Conforme aux protocoles")
                                                                                                                                                                                                                                                                                                    else:
                                                                                                                                                                                                                                                                                                                        st.warning("#### 🔴 Violation possible détectée")
                                                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                                                                                # Alerte WhatsApp si violation
                                                                                                                                                                                                                                                                                                                                                            if data.get("violation_detected"):
                                                                                                                                                                                                                                                                                                                                                                            st.markdown("#### 📱 Alerte de mobilisation")
                                                                                                                                                                                                                                                                                                                                                                                            if data.get("whatsapp_alert"):
                                                                                                                                                                                                                                                                                                                                                                                                                st.code(data["whatsapp_alert"], language="text")
                                                                                                                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                                                                                                                                    st.error(f"Erreur API: {response.status_code}")
                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                                                                                                    except requests.exceptions.Timeout:
                                                                                                                                                                                                                                                                                                                                                                                                                                                            st.error("⏱️ Délai d'attente dépassé. Veuillez réessayer.")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                except Exception as e:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                        st.error(f"❌ Erreur: {str(e)}")

                                                                                                                                                                                                                                                                                                                                                                                                                                                                        st.markdown("---")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                        st.markdown("**NExUS v2.0** - Powered by LECH Solidar 🚀✊")