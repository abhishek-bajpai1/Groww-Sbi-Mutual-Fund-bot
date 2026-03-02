import re

class IntentClassifier:
    ADVISORY_KEYWORDS = [
        r"should i invest",
        r"is .* good",
        r"is .* safe",
        r"best fund",
        r"compare returns",
        r"which is better",
        r"high return",
        r"safe investment",
        r"buy",
        r"sell",
        r"recommend",
        r"advice",
        r"suggest"
    ]

    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.ADVISORY_KEYWORDS]

    def is_advisory(self, query: str) -> bool:
        """ Returns True if the query is seeking financial advice. """
        for pattern in self.patterns:
            if pattern.search(query):
                return True
        return False

    def route_query(self, query: str) -> str:
        """ Routes query to 'rag' or 'refusal'. """
        if self.is_advisory(query):
            return "refusal"
        return "rag"

if __name__ == "__main__":
    classifier = IntentClassifier()
    test_queries = [
        "What is the expense ratio of SBI Large Cap?",
        "Should I invest in SBI Flexicap?",
        "Which is the best fund for high returns?",
        "How to download capital gains statement?"
    ]
    for q in test_queries:
        print(f"Query: {q} -> Route: {classifier.route_query(q)}")
