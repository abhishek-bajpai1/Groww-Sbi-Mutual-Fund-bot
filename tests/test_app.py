import unittest
import json
from unittest.mock import patch, MagicMock
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.classifier')
    @patch('app.get_rag')
    @patch('app.validator')
    def test_ask_factual(self, mock_validator, mock_get_rag, mock_classifier):
        # Setup mocks
        mock_classifier.route_query.return_value = "rag"
        
        mock_rag = MagicMock()
        mock_get_rag.return_value = mock_rag
        mock_rag.get_answer.return_value = {
            "answer": "Factual answer. Source: https://sbi.com Last updated from sources: Jan 2025",
            "source": "https://sbi.com",
            "scheme": "SBI Large Cap Fund",
            "last_updated": "Jan 2025"
        }
        
        mock_validator.validate_answer.return_value = True

        # Request
        response = self.app.post('/ask', 
                                 data=json.dumps({"query": "expense ratio"}),
                                 content_type='application/json')
        
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Factual answer", data['answer'])

    @patch('app.classifier')
    def test_ask_advisory(self, mock_classifier):
        mock_classifier.route_query.return_value = "refusal"

        response = self.app.post('/ask', 
                                 data=json.dumps({"query": "should i invest"}),
                                 content_type='application/json')
        
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 200)
        self.assertIn("cannot provide investment advice", data['answer'])

    def test_empty_query(self):
        response = self.app.post('/ask', 
                                 data=json.dumps({"query": ""}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)

if __name__ == "__main__":
    unittest.main()
