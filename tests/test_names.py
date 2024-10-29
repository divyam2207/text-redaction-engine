import pytest
from redactor import TextRedactor   

def test_redact_names():
    text = "Mr. John Doe went to the store. Contact him at john.doe@example.com."
    expected_redaction = "████████████ went to the store. Contact him at ████████████████████."

    redactor = TextRedactor()
    redacted_text = redactor.redact_text(text, concepts=None)

    assert redacted_text == expected_redaction

