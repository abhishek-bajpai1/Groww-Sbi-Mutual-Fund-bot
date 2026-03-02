import unittest
from unittest.mock import MagicMock, patch
from rag import RAGAssistant

class TestRAGAssistant(unittest.TestCase):
    @patch('rag.ChatGoogleGenerativeAI')
    @patch('rag.Chroma')
    @patch('rag.GoogleGenerativeAIEmbeddings')
    def test_get_answer_flow(self, mock_embeddings, mock_chroma, mock_llm):
        # Setup mocks
        mock_vectorstore = MagicMock()
        mock_chroma.return_value = mock_vectorstore
        
        mock_doc = MagicMock()
        mock_doc.page_content = "The expense ratio of SBI Large Cap is 0.95%."
        mock_doc.metadata = {"source_url": "https://sbimf.com/large-cap"}
        mock_vectorstore.similarity_search.return_value = [mock_doc]
        
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value.content = "Expense ratio is 0.95%. Source: https://sbimf.com/large-cap Last updated from sources: Jan 2025"

        # Initialize and test
        assistant = RAGAssistant()
        answer = assistant.get_answer("What is the expense ratio?")
        
        self.assertIn("0.95%", answer["answer"])
        self.assertEqual(answer["source"], "https://sbimf.com/large-cap")
        mock_vectorstore.similarity_search.assert_called_once()
        mock_llm_instance.invoke.assert_called_once()

    @patch('rag.Chroma')
    @patch('rag.GoogleGenerativeAIEmbeddings')
    def test_no_docs_found(self, mock_embeddings, mock_chroma):
        mock_vectorstore = MagicMock()
        mock_chroma.return_value = mock_vectorstore
        mock_vectorstore.similarity_search.return_value = []

        assistant = RAGAssistant()
        answer = assistant.get_answer("Something unknown")
        self.assertEqual(answer["answer"], "Information not available in official sources.")


if __name__ == "__main__":
    unittest.main()
