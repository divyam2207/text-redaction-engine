import pytest
import spacy
from redactor import redact_names, redact_dates, redact_phones, redact_addresses, redact_concept, nlp

# Load the spaCy model
# nlp = spacy.load("en_core_web_sm")

# Test redact_names function
def test_redact_names():
    doc = nlp("John Doe works at Acme Corp. His email is john.doe@example.com.")
    redacted_doc = redact_names(doc)
    assert "████ ███" in redacted_doc._.redacted_text
    assert "████.███@example.com" in redacted_doc._.redacted_text

# Test redact_dates function
def test_redact_dates():
    doc = nlp("The meeting is on July 4, 2023 at 2:30 PM.")
    redacted_doc = redact_dates(doc)
    assert "The meeting is on ████ ██ ████ at ████ ██." in redacted_doc._.redacted_text

# Test redact_phones function
def test_redact_phones():
    doc = nlp("Call me at 123-456-7890 or +1 (987) 654-3210.")
    redacted_doc = redact_phones(doc)
    assert "Call me at ████████████ or ██ ████ ██████████." in redacted_doc._.redacted_text

# Test redact_addresses function
def test_redact_addresses():
    doc = nlp("I live in New York City, USA.")
    redacted_doc = redact_addresses(doc)
    assert "I live in ███ ████ ████, ███." in redacted_doc._.redacted_text

# Test redact_concept function
def test_redact_concept():
    global concepts
    concepts = ["secret", "confidential"]
    doc = nlp("This is a secret and confidential document.")
    redacted_doc = redact_concept(doc)
    assert "This is a █████ and ████████████ document." in redacted_doc._.redacted_text

# Test full redaction pipeline
def test_full_redaction():
    global concepts
    concepts = ["secret"]
    text = "John Doe has a meeting on July 4, 2023 at 123 Main St, New York. Call 123-456-7890 for secret details."
    doc = nlp(text)
    doc = redact_dates(doc)
    doc = redact_names(doc)
    doc = redact_phones(doc)
    doc = redact_addresses(doc)
    doc = redact_concept(doc)
    
    expected = "████ ███ has a meeting on ████ ██ ████ at ███ ████ ███ ███ ████. Call ████████████ for █████ details."
    assert doc._.redacted_text == expected