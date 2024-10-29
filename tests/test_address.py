import pytest
from redactor import TextRedactor  

def test_redact_addresses():
    text = "My address is 123 Main St, Anytown, USA."
    expected_redaction = "My address is 123 ███████, ███████, ███."
    
    redactor = TextRedactor()
    redacted_text = redactor.redact_text(text, concepts=None)
    
    assert redacted_text == expected_redaction
    assert "Main St" in redactor.stats.addresses
