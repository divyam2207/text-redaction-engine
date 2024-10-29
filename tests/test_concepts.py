import pytest
from spacy.language import Language
from redactor import nlp



@pytest.fixture
def text_with_concepts():
    return "The capital of France is Paris, and it is known for its culture."

def test_redact_concepts(text_with_concepts):
    concepts = ["France", "culture"]
    doc = nlp(text_with_concepts)
    # Assume that 'redact_concept' is registered as a pipeline component
    doc = nlp.get_pipe("redact_concept")(doc)
    # Assume 'France' and 'culture' are redacted
    expected_redaction = "The capital of █████ is █████, and it is known for its █████."
    assert doc._.redacted_text == expected_redaction
