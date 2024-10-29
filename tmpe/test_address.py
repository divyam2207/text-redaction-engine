import pytest
from spacy.language import Language
import spacy

# Load the spaCy model and add your redact_addresses component
nlp = spacy.load("en_core_web_sm")

@pytest.fixture
def text_with_addresses():
    return "I live at 123 Main St, Springfield, IL, 62704."

def test_redact_addresses(text_with_addresses):
    doc = nlp(text_with_addresses)
    # Assume that 'redact_addresses' is registered as a pipeline component
    doc = nlp.get_pipe("redact_addresses")(doc)
    expected_redaction = "I live at █████ ███, ████████████, ██, █████."
    assert doc._.redacted_text == expected_redaction
