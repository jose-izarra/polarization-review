QUERY_GENERATION_PROMPT = (
    "Given a search query or claim, generate exactly 3 YouTube search queries to "
    "surface videos covering different perspectives on the topic: "
    "1) a query finding videos that support or argue for the claim, "
    "2) a query finding videos that oppose, criticise, or debunk the claim, "
    "3) a neutral debate or analysis framing of the same topic. "
    "For example, if the query is 'AI is beneficial for humanity', the queries should be: "
    "1) 'AI is beneficial for humanity' "
    "2) 'AI is harmful for humanity' "
    "3) 'AI is neutral on the topic of humanity' "
    "Another example where the query may be more ambiguous, such as 'Israel'"
    "the queries should be: "
    "1) 'Israel' "
    "2) 'Israel is a terrorist state' "
    "3) 'Israel is a peaceful country' "
    "Return a JSON array of exactly 3 short search strings. Return only valid JSON."
)

VIDEO_STANCE_PROMPT = (
    "For each video, determine its overall stance on the given topic. "
    "Return a JSON array where each element has: id (string), stance (-1/0/1). "
    "Use -1 for against, 0 for neutral, 1 for the topic. "
    "Return only valid JSON."
)
