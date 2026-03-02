import re

class Validator:
    def __init__(self):
        pass

    def validate_answer(self, answer: str) -> bool:
        """ Returns True if the answer meets all constraints. """
        # Constraint 1: Sentence count <= 3
        # Simple sentence splitter using period
        sentences = [s for s in re.split(r'(?<=[.!?])\s+', answer) if s]
        if len(sentences) > 3:
            return False

        # Constraint 2: Exactly one URL
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', answer)
        if len(urls) != 1:
            return False

        # Constraint 3: Contains "Last updated from sources:"
        if "Last updated from sources:" not in answer:
            return False

        return True

    def sanitize_answer(self, answer: str) -> str:
        """ Attempts to trim the answer if it exceeds constraints. """
        sentences = [s for s in re.split(r'(?<=[.!?])\s+', answer) if s]
        if len(sentences) > 3:
            answer = " ".join(sentences[:3])
            # Ensure it still has a URL if it was in the later sentences (tricky)
            # This is why the prompt is key.
        return answer

if __name__ == "__main__":
    validator = Validator()
    valid_ans = "The expense ratio of SBI Large Cap is 0.95%. For more details, visit the official page. Source: https://sbimf.com Last updated from sources: Jan 2025"
    invalid_ans = "This is a very long answer with more than three sentences. Here is the second sentence. Here is the third. Here is the fourth. Source: https://sbimf.com Last updated from sources: Jan 2025"
    print(f"Valid: {validator.validate_answer(valid_ans)}")
    print(f"Invalid: {validator.validate_answer(invalid_ans)}")
