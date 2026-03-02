import unittest
import re
from validator import Validator

class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = Validator()

    def test_valid_answer(self):
        ans = "The expense ratio is 0.95%. You can check more details on the official site. Source: https://sbimf.com Last updated from sources: Jan 2025"
        self.assertTrue(self.validator.validate_answer(ans))

    def test_invalid_sentence_count(self):
        ans = "Sentence one. Sentence two. Sentence three. Sentence four. Source: https://sbimf.com Last updated from sources: Jan 2025"
        self.assertFalse(self.validator.validate_answer(ans))

    def test_missing_url(self):
        ans = "The expense ratio is 0.95%. It is very low. Last updated from sources: Jan 2025"
        self.assertFalse(self.validator.validate_answer(ans))

    def test_multiple_urls(self):
        ans = "Check here: https://sbimf.com and here: https://groww.in. Last updated from sources: Jan 2025"
        self.assertFalse(self.validator.validate_answer(ans))

    def test_missing_disclaimer(self):
        ans = "The expense ratio is 0.95%. Source: https://sbimf.com"
        self.assertFalse(self.validator.validate_answer(ans))

    def test_sanitize_answer(self):
        long_ans = "One. Two. Three. Four. Five. Source: https://sbimf.com Last updated from sources: Jan 2025"
        sanitized = self.validator.sanitize_answer(long_ans)
        sentences = [s for s in re.split(r'(?<=[.!?])\s+', sanitized) if s]
        self.assertLessEqual(len(sentences), 3)

if __name__ == "__main__":
    unittest.main()
