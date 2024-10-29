import pytest
from redactor import TextRedactor 
def test_redact_phones():
    text = "You can reach me at (123) 456-7890 or +1-234-567-8901."
    expected_redaction = "You can reach me at ██████████████ or ███████████████."
    
    redactor = TextRedactor()
    redacted_text = redactor.redact_text(text, concepts=None)
    
    assert redacted_text == expected_redaction
    assert "(123) 456-7890" in redactor.stats.phones
