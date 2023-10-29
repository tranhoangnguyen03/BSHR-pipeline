import streamlit as st
from st_components.bshr import bshr

st.title('BSHR Visualizer')

query = st.text_input('input your query')
if st.button('Ask'):
    answer = bshr(query)
    st.write(answer)