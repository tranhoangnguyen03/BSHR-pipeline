import openai
import requests
from loguru import logger
from utils.prompt_templates import BSHRTemplates
from utils.text_utils import Utils
from bs4 import BeautifulSoup
from tenacity import retry, wait_exponential, retry_if_exception_type

class OpenAIHelper:
    def __init__(self, model, headers):
        self.model = model
        self.headers = headers

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), 
           retry=retry_if_exception_type(openai.error.RateLimitError))
    def openai_response(self, system_prompt, user_prompt):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return openai.ChatCompletion.create(model=self.model, messages=messages, headers=self.headers)

class Brainstormer(OpenAIHelper):
    def __init__(self, openai_model, headers):
        self.model = openai_model
        self.headers = headers

    def generate_queries(self, main_query, n=5):
        logger.info(f"\nBrainstorming search queries for: {main_query}")
        
        system_prompt= BSHRTemplates.BRAINSTORM.replace('<number>', f'{n}')
        user_prompt= f"Brainstorm {n} search queries based on the topic: {main_query}."
        
        response = self.openai_response(system_prompt, user_prompt)

        search_queries = response.choices[0].message['content'].split("\n")
        logger.info(f"Generated search queries: {search_queries}")
        return search_queries[:n]

class Searcher:
    def __init__(self, openai_model, headers, searx_url):
        self.model = openai_model
        self.headers = headers
        self.searx_url = searx_url

    def search_searx(self, query):
        logger.info(f"Searching Searx for: {query}")
        search_params = {
            'q': query,
            'format': 'json'
        }

        response = requests.get(self.searx_url, params=search_params)
        data = response.json()

        # Check if there are search results
        if not data['results']:
            logger.warning(f"No results found on Searx for: {query}")
            return None  # Return None if no results are found

        # Get the URL of the first result
        result_url = data['results'][0]['url']
        page_response = requests.get(result_url)

        # Use BeautifulSoup to parse the page
        soup = BeautifulSoup(page_response.content, 'html.parser')

        page_content = soup.get_text()
        # Remove excessive whitespace and newline characters
        page_content = ' '.join(page_content.split())
        # Extract the main content and limit to 400 words or less
        limited_content = ' '.join(page_content.split()[:400])

        logger.info(f"Extracted limited page content from URL: {result_url}")

        return limited_content

    def search_wikipedia(self, query):
        logger.info(f"\nSearching Wikipedia for: {query}")
        url = 'https://en.wikipedia.org/w/api.php'
        search_params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query,
            'format': 'json'
        }

        response = requests.get(url, params=search_params)
        data = response.json()

        # Check if there are search results
        if not data['query']['search']:
            logger.warning(f"No results found on Wikipedia for: {query}")
            return None  # Return None if no results are found

        # Get the title of the first result
        title = data['query']['search'][0]['title']

        content_params = {
            'action': 'query',
            'prop': 'extracts',
            'exintro': True,
            'explaintext': True,
            'titles': title,
            'format': 'json'
        }

        response = requests.get(url, params=content_params)
        data = response.json()

        # Get the page ID of the first page
        page_id = list(data['query']['pages'].keys())[0]

        # Extract content of the page
        results = data['query']['pages'][page_id]['extract']
        logger.info(f"Extracted Wikipedia content for: {title}")

        return results

    def search(self, queries):
        cleaned_queries = [
            Utils.clean_search_query(query)
            for query in queries
        ]
        # Search Wikipedia
        wikipedia_results = [
            self.search_wikipedia(query) 
            for query in cleaned_queries 
            if self.search_wikipedia(query) is not None
        ]

        # Search Searx
        searx_results = [
            self.search_searx(query) 
            for query in cleaned_queries 
            if self.search_searx(query) is not None
        ]

        # Merge results from both sources
        all_search_results = wikipedia_results + searx_results

        return all_search_results
        


class InformationProcessor(OpenAIHelper):
    def __init__(self, openai_model, headers):
        self.model = openai_model
        self.headers = headers

    def relevancy_check(self, content, search_query, main_query):
        logger.info(f"Checking relevance of content '{content}' for the query: '{search_query}'")
        system_prompt = BSHRTemplates.YES_NO_MACHINE
        user_prompt = f"Is the content below relevant to the query '{search_query}' of topic '{main_query}'? \n'{content}' "
        response = self.openai_response(system_prompt, user_prompt)
        relevance_response = response.choices[0].message['content'].lower()
        return 'yes' in relevance_response or 'relevant' in relevance_response  # Returns True if the title is relevant, False otherwise.

    def condense(self, content, main_query):
        logger.info(f"Condensing information")
        system_prompt = BSHRTemplates.CONDENSER
        user_prompt = f"TOPIC: {main_query}. \nCONTENT: {content} \n CONDENSED: "
        response = self.openai_response(system_prompt, user_prompt)
        
        try:
            condensed_content = response.choices[0].message['content']
            logger.info(f"Condensed content: {condensed_content}")
            return condensed_content
        except Exception as e:
            logger.warning(f"Error {e} while trying to condense content: {content}")
            return None

    def generate_hypothesis(self, search_results, main_query):
        logger.info(f"Generating hypothesis for search results")

        system_prompt = BSHRTemplates.HYPOTHESIZE
        user_prompt = f"Based on the following search results, formulate a hypothesis to answer the query '{main_query}':\n{search_results}"
        response = self.openai_response(system_prompt, user_prompt)

        hypothesis = response.choices[0].message['content']
        logger.info(f"Generated hypothesis: {hypothesis}")
        return hypothesis

class HypothesisTournament(OpenAIHelper):
    def __init__(self, openai_model, headers):
        self.model = openai_model
        self.headers = headers

        self.processor = InformationProcessor(self.model, self.headers)

    def compete_hypotheses(self, hypothesis_a, hypothesis_b, main_query):
        logger.info(f"\nComparing hypothesis A: '{hypothesis_a}' with hypothesis B: '{hypothesis_b}'")
        
        system_prompt = BSHRTemplates.REFINE
        user_prompt = f"The current inquiry is '{main_query}'. Refine and merge the following hypotheses to create a superior hypothesis:\n1. {hypothesis_a}\n2. {hypothesis_b}"
        response = self.openai_response(system_prompt, user_prompt)
        refined_hypothesis = response.choices[0].message['content']
        
        # Condense the hypothesis
        refined_hypothesis = self.processor.condense(refined_hypothesis, main_query)
        logger.info(f"Refined hypothesis: {refined_hypothesis}")
        return refined_hypothesis

    def run_tournament(self, hypotheses, main_query):
        """
        Conduct a tournament to determine the best hypothesis.

        The tournament is structured as follows:
        1. Pair up hypotheses to compete against each other.
        2. Use OpenAI GPT to determine the winner of each pair.
        3. If there is an odd number of hypotheses, the last one gets a bye to the next round.
        4. Repeat the process until one hypothesis remains.

        :param hypotheses: List of hypotheses to compete.
        :return: The winning hypothesis.
        """
        logger.info(f"\nStarting hypothesis tournament with {len(hypotheses)} hypotheses")
        while len(hypotheses) > 1:
            next_round_hypotheses = []
            for i in range(0, len(hypotheses), 2):
                if i + 1 < len(hypotheses):
                    winner_hypothesis = self.compete_hypotheses(hypotheses[i], hypotheses[i + 1], main_query)
                    next_round_hypotheses.append(winner_hypothesis)
                else:
                    # If an odd number of hypotheses, pass the last one to the next round.
                    next_round_hypotheses.append(hypotheses[i])
            hypotheses = next_round_hypotheses
        winner = hypotheses[0]
        logger.info(f"Winner of the tournament: {winner}")
        return winner

class Responder(OpenAIHelper):
    def __init__(self, openai_model, headers):
        self.model = openai_model
        self.headers = headers

    def generate_response(self, context, final_hypothesis):
        logger.info(f"\nCrafting a conversational response for the final hypothesis")
        system_prompt = BSHRTemplates.RESPOND
        user_prompt = (
            f"{context}\n\n Answer Cues: {final_hypothesis}\n\n"
            "Please provide an elaborate answer. Make use of the provided answer cues "
            "to form a information-rich and comprehensive response for the end-user."
        )
        response = self.openai_response(system_prompt, user_prompt)

        conversational_answer = response.choices[0].message['content']
        logger.info(f"Conversational response: {conversational_answer}")
        return conversational_answer