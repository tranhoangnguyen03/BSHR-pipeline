# BSHR Streamlit App 

This is a Streamlit app that utilizes the Brainstorm-Search-Hypothesize-Refine (BSHR) pipeline to answer user queries.

## Overview

The app has two main components:

- `app.py`: The Streamlit frontend that takes a query input and displays the BSHR response. 

- `st_components/bshr.py`: Wrapper functions to call the BSHR pipeline. Provides both the full BSHR pipeline as well as a simpler "vanilla" GPT-3 response.

The main BSHR pipeline code lives in `BSHR/bshr_pipeline.py`. It brings together the different components:

- Brainstormer: Generates search queries using GPT-3 based on the main query.

- Searcher: Searches Wikipedia and a Searx instance using the generated queries.

- InformationProcessor: Checks relevancy of results, condenses information, and generates hypotheses.

- HypothesisTournament: Refines hypotheses through a tournament to determine the best one. 

- Responder: Crafts a conversational response using the final hypothesis.


The pipeline uses the OpenAI API, with the option to mock requests for testing using https://openrouter.ai.

## Requirements
Make sure to install requirements before running the app:
```
pip install -r requirements.txt
```

## Configuration

The app expects a `.streamlit/secrets.toml` file with the following:

```
[openai]
api_key="sk-..." 
api_base= ... # "https://api.openai.com/v1" or "https://openrouter.ai/api/v1"
base_model= ... # model_name 
mock_openai= ... # false for true OpenAI, true for openrouter or other openai mock servers

[search]
searx = ... # your own searx server
```
**You need to manually create this file and fill in your own OpenAI API key and other settings.**

## Running the App

With the secrets configured:

```
streamlit run app.py
```

The main query can then be entered and the BSHR pipeline will be invoked to generate a response.

## Customizing 

The different pipeline components in `bshr_pipeline.py` can be configured or swapped out as needed. New question answering strategies can be built by mixing and matching the different modules.
