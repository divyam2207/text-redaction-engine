import pytest
from spacy.language import Language
import spacy
from redactor import *

# Load the spaCy model and add your redact_names component

@pytest.fixture
def text_with_names():
    return "Hello, my name is John Doe and I met with Alice Wonderland yesterday."

def test_redact_names(text_with_names):
    doc = nlp(text_with_names)
    # Assume that 'redact_names' is registered as a pipeline component
    doc = redact_names(doc)
    print(doc._.redacted_text)
    expected_redaction = "Hello, my name is ██████ ████ and I met with ████████████ yesterday."
    assert doc._.redacted_text == expected_redaction
