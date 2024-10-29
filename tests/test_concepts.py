import pytest
from redactor import TextRedactor 

def test_redact_concepts():
    text = "The quick brown fox jumps over the lazy dog."
    concepts = ["quick", "lazy"]
    expected_redaction = "The █████ brown fox jumps over the ████ dog."
    
    redactor = TextRedactor()
    redacted_text = redactor.redact_text(text, concepts=concepts)
    
    assert redacted_text == expected_redaction
    assert "quick" in redactor.stats.concepts
    assert "lazy" in redactor.stats.concepts
