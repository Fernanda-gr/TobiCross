import streamlit as st

st.title("TobiCross")
st.caption("Recomendador de anime para principiantes")
prompt = st.chat_input("¿Qué películas te gustan?")

if prompt:
    st.write("¿Qué películas te gustan? : ",prompt)
