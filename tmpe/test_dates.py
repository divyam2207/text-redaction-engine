import pytest
from spacy.language import Language
import spacy
from redactor import nlp

# Load the spaCy model and add your redact_dates component


@pytest.fixture
def text_with_dates():
    return (
        "Important dates include 3 Jul 2000, 01/15/2021, and Mon, 3 Jul 2000 07:57:00 -0700 (PDT)."
    )

def test_redact_dates(text_with_dates):
    doc = nlp(text_with_dates)
    # Assume that 'redact_dates' is registered as a pipeline component
    doc = nlp.get_pipe("redact_dates")(doc)
    expected_redaction = (
        "Important dates include ███ ███ ████, ██/██/████, and ███, █ █ ███ ███ ████████."
    )
    assert doc._.redacted_text == expected_redaction
