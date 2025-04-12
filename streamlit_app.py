import streamlit as st

# Afficher tous les secrets pour tester
st.write("🔐 Voici les secrets chargés :")
st.write(st.secrets)

# Accéder aux secrets et tester
db_username = st.secrets["DB_USERNAME"]
st.write(f"DB_USERNAME: {db_username}")
