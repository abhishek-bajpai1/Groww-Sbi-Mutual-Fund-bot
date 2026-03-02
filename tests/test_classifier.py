import unittest
from classifier import IntentClassifier

class TestIntentClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = IntentClassifier()

    def test_factual_queries(self):
        factual_queries = [
            "What is the expense ratio of SBI Large Cap?",
            "What is the lock-in period for SBI Long Term Equity Fund?",
            "How to download capital-gains statement?",
            "Exit load of SBI Flexicap"
        ]
        for q in factual_queries:
            self.assertEqual(self.classifier.route_query(q), "rag", f"Failed for query: {q}")

    def test_advisory_queries(self):
        advisory_queries = [
            "Should I invest in SBI Large Cap?",
            "Is SBI Flexicap a good fund?",
            "Which is the best fund for high returns?",
            "Suggest some safe investments",
            "Give me some investment advice"
        ]
        for q in advisory_queries:
            self.assertEqual(self.classifier.route_query(q), "refusal", f"Failed for query: {q}")

    def test_case_insensitivity(self):
        self.assertEqual(self.classifier.route_query("SHOULD I INVEST"), "refusal")
        self.assertEqual(self.classifier.route_query("EXPENSE RATIO"), "rag")

if __name__ == "__main__":
    unittest.main()
