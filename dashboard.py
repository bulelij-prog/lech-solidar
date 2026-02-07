import streamlit as st

st.set_page_config(page_title="LECH Solidar", page_icon="✊")

URL = st.secrets.get("CLOUD_FUNCTION_URL", "")
PROJECT = st.secrets.get("PROJECT_ID", "")
STORE = st.secrets.get("DATA_STORE_ID", "")

st.title("✊ LECH Solidar - TEST")
st.write(f"Secrets loaded: {bool(URL and PROJECT and STORE)}")
