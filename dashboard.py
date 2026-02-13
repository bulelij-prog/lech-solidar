import streamlit as st
from vertexai.generative_models import GenerativeModel, GenerativeModel
import vertexai

# Configure Streamlit page
st.set_page_config(
    page_title="NExUS v2.5 - CGSP",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure custom theme with CGSP red color
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #E63946;
        color: white;
    }
    .stButton>button:hover {
        background-color: #d62828;
    }
    h1 {
        color: #E63946;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Vertex AI
vertexai.init(project="syndicat-novembre-2025", location="europe-west1")

def main():
    st.title(" NExUS v2.5 - CGSP")
    st.markdown("### Plateforme d'Intelligence Artificielle pour la CGSP")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        Bienvenue sur **NExUS v2.5**, la plateforme d'IA gnrative ddie aux syndicats.
        
        **Fonctionnalits :**
        -  Analyse de textes avec Gemini
        -  Traitement de documents
        -  Chat intelligent
        """)
        
        user_input = st.text_area(
            "Posez votre question ou collez votre texte :",
            height=150,
            placeholder="Entrez votre texte ici..."
        )
        
        if st.button(" Analyser", use_container_width=True):
            if user_input:
                try:
                    with st.spinner(" Traitement en cours..."):
                        model = GenerativeModel("gemini-1.5-pro")
                        response = model.generate_content(user_input)
                        
                        st.success(" Analyse termine")
                        st.markdown("### Rsultat :")
                        st.write(response.text)
                except Exception as e:
                    st.error(f" Erreur : {str(e)}")
            else:
                st.warning(" Veuillez entrer du texte")
    
    with col2:
        st.markdown("###  Infos Systme")
        st.info("""
        **Version :** v2.5
        
        **Modle :** Gemini 1.5 Pro
        
        **Rgion :** europe-west1
        
        **Statut :**  SYSTEM OK
        """)

if __name__ == "__main__":
    main()
