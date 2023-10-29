import streamlit as st
from BSHR.bshr_pipeline import BSHRPipeline

def bshr(query):
    pipeline = BSHRPipeline(
        api_key= st.secrets.openai.api_key,
        api_base= st.secrets.openai.api_base,
        model = st.secrets.openai.base_model,
        searx_url = st.secrets.search.searx_url,
        mock_open_ai= st.secrets.openai.mock_openai,
    )
    response = pipeline.run(query)
    return response


def vanilla(query):
    from utils.prompt_templates import BSHRTemplates
    pipeline = BSHRPipeline(
        api_key= st.secrets.openai.api_key,
        api_base= st.secrets.openai.api_base,
        model= st.secrets.openai.base_model,
        searx_url = st.secrets.search.searx_url,
        mock_open_ai= st.secrets.openai.mock_openai,
    )
    
    system_prompt= BSHRTemplates.RESPOND
    user_prompt= f"Please use your best knowledge to form a long and substantial answer to the question: {query}."
    response = pipeline.responder.openai_response(system_prompt, user_prompt)

    return response