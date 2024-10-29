import pytest
from redactor import TextRedactor  

def test_redact_dates():
    text = "The meeting is scheduled for Jan 15, 2024."
    expected_redaction = "The meeting is scheduled for ████████████."
    
    redactor = TextRedactor()
    redacted_text = redactor.redact_text(text, concepts=None)
    
    assert redacted_text == expected_redaction
    assert "Jan 15, 2024" in redactor.stats.dates
