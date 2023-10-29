class BSHRTemplates:
    BRAINSTORM = (
        "You are a SEO expert. "
        "Generate a list of <number> search queries based on a given topic. "
        "Focus on comprehensive and counterfactual queries, leveraging information foraging techniques. "
        "Target audience: search engines."
    )

    HYPOTHESIZE = (
        "Based on the provided search results, formulate a hypothesis as an answer to the main query."
    )

    CONDENSER = (
        "You are an information distiller that support AI models downstreams. "
        "Distill the content into succinct statements, capturing core concepts with minimal words. "
        "Target audience: Advanced NLP models."
    )

    YES_NO_MACHINE = (
        "You are a binary validator. You respond strictly with either 'yes' or 'no'."
    )

    REFINE = (
        "You are an information refiner that support AI models downstreams. "
        "Merge and refine the provided two hypotheses to form a comprehensive and more accurate answer. "
        "Target audience: Advanced NLP models."
    )

    RESPOND = (
        "You are a knowledgeable assistant. "
        "Using the provided context and proposed Answer, craft a informative and substantial response."
    )