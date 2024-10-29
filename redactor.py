import spacy
from spacy.language import Language
import re
import argparse
import os
import glob
from typing import List, Set
from dataclasses import dataclass, field

@dataclass
class RedactionStats:
    names: Set[str] = field(default_factory=set)
    dates: Set[str] = field(default_factory=set)
    phones: Set[str] = field(default_factory=set)
    addresses: Set[str] = field(default_factory=set)
    concepts: Set[str] = field(default_factory=set)

class TextRedactor:
    def __init__(self, model_name: str = "en_core_web_md"):
        self.nlp = spacy.load(model_name)
        self.stats = RedactionStats()
        self._setup_extensions()
        self._register_pipeline_components()
        self._setup_pipeline()
        self.concepts = set()

    def _setup_extensions(self):
        """Setup custom extensions for spaCy"""
        if not spacy.tokens.Doc.has_extension("redacted_text"):
            spacy.tokens.Doc.set_extension("redacted_text", default="")
        if not spacy.tokens.Doc.has_extension("redaction_spans"):
            spacy.tokens.Doc.set_extension("redaction_spans", default=[])
        if not spacy.tokens.Doc.has_extension("stats"):
            spacy.tokens.Doc.set_extension("stats", default=None)
        if not spacy.tokens.Doc.has_extension("concepts"):
            spacy.tokens.Doc.set_extension("concepts", default=set())

    def _register_pipeline_components(self):
        """Register the pipeline components with spaCy"""
        @Language.component("redact_names")
        def redact_names(doc):
            redacted_text = doc._.redacted_text
            spans_to_redact = []
            stats = doc._.stats

            if stats is None:
                stats = RedactionStats()
                doc._.stats = stats

            # Detect named entities
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG"]:
                    spans_to_redact.append((ent.start_char, ent.end_char))
                    stats.names.add(ent.text)

            # Additional patterns for names
            patterns = [
                r'(?i)(?:mr\.|mrs\.|ms\.|dr\.|prof\.)\s+[a-z]+(?:\s+[a-z]+)?',
                r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}',
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            ]

            for pattern in patterns:
                for match in re.finditer(pattern, redacted_text):
                    spans_to_redact.append((match.start(), match.end()))
                    stats.names.add(match.group())

            doc._.redacted_text = TextRedactor._apply_redaction(redacted_text, spans_to_redact)
            doc._.redaction_spans.extend(spans_to_redact)
            return doc

        @Language.component("redact_dates")
        def redact_dates(doc):
            redacted_text = doc._.redacted_text
            spans_to_redact = []
            stats = doc._.stats

            if stats is None:
                stats = RedactionStats()
                doc._.stats = stats

            date_patterns = [
                r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
                r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
                r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|'
                r'Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b',
                r'\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s?\d{1,2}\s'
                r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s\d{4}\b',
                r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
                r'\b(?:19|20)\d{2}\b'
            ]

            for pattern in date_patterns:
                for match in re.finditer(pattern, redacted_text, re.IGNORECASE):
                    spans_to_redact.append((match.start(), match.end()))
                    stats.dates.add(match.group())

            for ent in doc.ents:
                if ent.label_ in ["DATE", "TIME"]:
                    spans_to_redact.append((ent.start_char, ent.end_char))
                    stats.dates.add(ent.text)

            doc._.redacted_text = TextRedactor._apply_redaction(redacted_text, spans_to_redact)
            doc._.redaction_spans.extend(spans_to_redact)
            return doc

        @Language.component("redact_phones")
        def redact_phones(doc):
            redacted_text = doc._.redacted_text
            spans_to_redact = []
            stats = doc._.stats

            phone_patterns = [
                r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
                r'\b\d{3}[-.\s]?\d{4}\b',
                r'\+\d{1,3}\s?\d{10,}'
            ]

            for pattern in phone_patterns:
                for match in re.finditer(pattern, redacted_text):
                    spans_to_redact.append((match.start(), match.end()))
                    stats.phones.add(match.group())

            doc._.redacted_text = TextRedactor._apply_redaction(redacted_text, spans_to_redact)
            doc._.redaction_spans.extend(spans_to_redact)
            return doc

        @Language.component("redact_addresses")
        def redact_addresses(doc):
            redacted_text = doc._.redacted_text
            spans_to_redact = []
            stats = doc._.stats

            address_patterns = [
                r'\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b',
                r'\b[A-Z]{2}\s+\d{5}(?:-\d{4})?\b',
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2}\b'
            ]

            for pattern in address_patterns:
                for match in re.finditer(pattern, redacted_text):
                    spans_to_redact.append((match.start(), match.end()))
                    stats.addresses.add(match.group())

            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC", "FAC"]:
                    spans_to_redact.append((ent.start_char, ent.end_char))
                    stats.addresses.add(ent.text)

            doc._.redacted_text = TextRedactor._apply_redaction(redacted_text, spans_to_redact)
            doc._.redaction_spans.extend(spans_to_redact)
            return doc

        @Language.component("redact_concepts")
        def redact_concepts(doc):
            redacted_text = doc._.redacted_text
            spans_to_redact = []
            stats = doc._.stats
            concepts = doc._.concepts

            if concepts:
                concept_pattern = r'\b(?:' + '|'.join(map(re.escape, concepts)) + r')\b'
                for match in re.finditer(concept_pattern, redacted_text, re.IGNORECASE):
                    spans_to_redact.append((match.start(), match.end()))
                    stats.concepts.add(match.group())

            doc._.redacted_text = TextRedactor._apply_redaction(redacted_text, spans_to_redact)
            doc._.redaction_spans.extend(spans_to_redact)
            return doc

    def _setup_pipeline(self):
        """Configure the NLP pipeline with custom components"""
        # Remove existing custom components if they exist
        component_names = ["redact_names", "redact_dates", "redact_phones", 
                         "redact_addresses", "redact_concepts"]
        for name in component_names:
            if name in self.nlp.pipe_names:
                self.nlp.remove_pipe(name)

        # Add components in correct order
        self.nlp.add_pipe("redact_names", after="ner")
        self.nlp.add_pipe("redact_dates", after="redact_names")
        self.nlp.add_pipe("redact_phones", after="redact_dates")
        self.nlp.add_pipe("redact_addresses", after="redact_phones")
        self.nlp.add_pipe("redact_concepts", last=True)

    @staticmethod
    def _apply_redaction(text: str, spans: List[tuple]) -> str:
        """Apply redaction to text while handling overlapping spans"""
        if not spans:
            return text

        # Sort spans and merge overlapping ones
        spans.sort(key=lambda x: x[0])
        merged_spans = []
        current_span = list(spans[0])

        for start, end in spans[1:]:
            if start <= current_span[1]:
                current_span[1] = max(current_span[1], end)
            else:
                merged_spans.append(tuple(current_span))
                current_span = [start, end]
        merged_spans.append(tuple(current_span))

        # Apply redaction
        result = []
        last_end = 0
        for start, end in merged_spans:
            result.append(text[last_end:start])
            result.append('█' * (end - start))
            last_end = end
        result.append(text[last_end:])

        return ''.join(result)

    def redact_text(self, text: str, concepts: List[str] = None) -> str:
        """Main method to redact text"""
        # Initialize document extensions
        doc = self.nlp.make_doc(text)
        doc._.redacted_text = text
        doc._.stats = RedactionStats()  # Initialize with a new RedactionStats object
        doc._.concepts = set(concepts) if concepts else set()
        
        # Process through pipeline
        doc = self.nlp(doc)  # Pass the doc object instead of text
        self.stats = doc._.stats
        return doc._.redacted_text

def main():
    parser = argparse.ArgumentParser(description="Enhanced text redaction system")
    parser.add_argument('--input', help="Input file pattern (e.g., *.txt)")
    parser.add_argument('--names', action='store_true', help='Redact names')
    parser.add_argument('--dates', action='store_true', help='Redact dates')
    parser.add_argument('--phones', action='store_true', help='Redact phone numbers')
    parser.add_argument('--address', action='store_true', help='Redact addresses')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--concept', action='append', help='Concepts to redact')
    parser.add_argument('--stats', help="Stats output file")
    
    args = parser.parse_args()
    
    # Initialize redactor
    redactor = TextRedactor()
    redactor.stats = RedactionStats() 
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Process input files
    input_files = glob.glob(args.input) if args.input else glob.glob('*.txt')
    
    for input_file in input_files:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Perform redaction
        redacted_text = redactor.redact_text(text, args.concept)
        
        # Write output
        output_path = os.path.join(args.output, os.path.basename(input_file) + '.redacted')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(redacted_text)
    print(redactor.stats.names)
    
    # Write stats if requested
    if args.stats:
        with open(args.stats, 'w', encoding='utf-8') as f:
            f.write("Redaction Statistics:\n")
            f.write(f"Names: {sorted(redactor.stats.names)}\n")
            f.write(f"Dates: {sorted(redactor.stats.dates)}\n")
            f.write(f"Phones: {sorted(redactor.stats.phones)}\n")
            f.write(f"Addresses: {sorted(redactor.stats.addresses)}\n")
            f.write(f"Concepts: {sorted(redactor.stats.concepts)}\n")

if __name__ == "__main__":
    main()