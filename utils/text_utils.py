import re
class Utils:
    @staticmethod
    def clean_search_query(query):
        # Remove the preceding numbers and period
        cleaned = re.sub(r"^\d+\.\s*", "", query)
        # Remove surrounding quotes
        cleaned = cleaned.strip("\"")
        return cleaned