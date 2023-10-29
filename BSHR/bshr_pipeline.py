from BSHR.components import (
    Brainstormer, Searcher, InformationProcessor, HypothesisTournament, Responder
)
from loguru import logger
import openai
import os

class BSHRPipeline:
    def __init__(self, api_key, api_base, model, searx_url, mock_open_ai=True):
        openai.api_key = api_key
        if mock_open_ai:
            openai.api_base = api_base or "https://openrouter.ai/api/v1"
            self.model = model or 'mistralai/mistral-7b-instruct'
            self.headers={
                "HTTP-Referer": 'http://localhost:3000', # To identify your app. Can be set to e.g. http://localhost:3000 for testing
                "X-Title": 'BSHRPipeline', # Optional. Shows on openrouter.ai
            }
        else:
            self.model = model or 'gpt-3.5-turbo'
            self.headers={}

        self.searx_url = searx_url
        logger.info("Initialized BSHRPipeline")

        self.brainstormer = Brainstormer(self.model, self.headers)
        self.searcher = Searcher(self.model, self.headers, self.searx_url)
        self.processor = InformationProcessor(self.model, self.headers)
        self.tournament = HypothesisTournament(self.model, self.headers)
        self.responder = Responder(self.model, self.headers)

    def run(self, main_query):
        logger.info(f"Running the pipeline for main query: {main_query}")
        # Step 1: Brainstorming
        search_queries = self.brainstormer.generate_queries(main_query, n=4)

        # Step 2 & 3: Searching and Hypothesizing
        search_results = self.searcher.search(search_queries)
        
        condensed_search_results = [
            self.processor.condense(result, main_query) 
            for result in search_results
        ]

        condensed_n_relevant_search_results = [   
            self.processor.relevancy_check(content, search_query, main_query) 
            for content, search_query in zip(condensed_search_results, search_queries)
        ]
        
        hypotheses = [
            self.processor.generate_hypothesis(result, main_query) 
            for result in condensed_n_relevant_search_results
        ]

        condensed_hypotheses = [
            self.processor.condense(hypothesis, main_query)
                for hypothesis in hypotheses
        ]

        # Step 4: Refining through Hypothesis Tournament
        final_hypothesis = self.tournament.run_tournament(
            condensed_hypotheses, main_query
        ) 

        final_response = self.responder.generate_response(
            context = f'Question: {main_query}',
            final_hypothesis = final_hypothesis
        )

        print('\n\n------------ Summaries ------------')
        print(f"----- Main Query: \n{main_query}")
        print(f"----- Search Queries: ")
        print(search_queries)
        print(f"----- Hypotheses: ") 
        print(condensed_hypotheses)
        print(f"----- Final Hypothesis: \n{final_hypothesis}")

        print('\n\n------------ FINAL RESPONSE ------------')
        print(final_response)
        return final_response
