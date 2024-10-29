import pytest
import re
from spacy.language import Language
import spacy

# Load the spaCy model and add your redact_phones component
nlp = spacy.load("en_core_web_sm")

@pytest.fixture
def text_with_phones():
    return "You can reach me at (123) 456-7890 or +1 234 567 8901."

def test_redact_phones(text_with_phones):
    doc = nlp(text_with_phones)
    # Assume that 'redact_phones' is registered as a pipeline component
    doc = nlp.get_pipe("redact_phones")(doc)
    expected_redaction = "You can reach me at ████████ or ████████."
    assert doc._.redacted_text == expected_redaction
