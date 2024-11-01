import spacy
from spacy.language import Language
import re
import argparse
import os
import sys
from datetime import datetime
import glob
from typing import List, Set, Dict
from dataclasses import dataclass, field
import json
import nltk #for advance concept redaction
nltk.download("omw-1.4")
nltk.download("wordnet")
from nltk.corpus import wordnet

@dataclass
class RedactionItem:
    text: str
    start_idx: int
    end_idx: int
    category: str

@dataclass
class FileStats:
    filename: str
    total_ch: int
    total_redaction: int
    redacted_items: List[RedactionItem] = field(default_factory=list)
    

@dataclass
class RedactionStats:
    names: Set[str] = field(default_factory=set)
    dates: Set[str] = field(default_factory=set)
    phones: Set[str] = field(default_factory=set)
    addresses: Set[str] = field(default_factory=set)
    concepts: Set[str] = field(default_factory=set)
    file_stats: Dict[str, FileStats] = field(default_factory=dict)

    #function to get the stats
    def statsDict(self):

        return {
            'summary': {
                'names': {
                    'count': len(self.names),
                    'items': sorted(list(self.names))
                },
                'dates': {
                    'count': len(self.dates),
                    'items': sorted(list(self.dates))
                },
                'phones': {
                    'count': len(self.phones),
                    'items': sorted(list(self.phones))
                },
                'addresses': {
                    'count': len(self.addresses),
                    'items': sorted(list(self.addresses))
                },
                'concepts': {
                    'count': len(self.concepts),
                    'items': sorted(list(self.concepts))
                },

            },
            'files': {
                filename: {
                    'total_chars': stats.total_ch,
                    'total_redaction': stats.total_redaction,
                    'redacted_items': [
                        {
                            'text': item.text,
                            'start_index': item.start_idx,
                            'end_index': item.end_idx,
                            'category': item.category
                        }
                        for item in stats.redacted_items
                    ]
                }
                for filename, stats in self.file_stats.items()
            }
        }
    
    #writing stats to the mentioned stream/file
    def write_stats(self, output):

        stats_data = self.statsDict()
        formatted_stats = self._formatStats(stats_data)

        if output in ('stdout', 'stderr'):
            op_stream = sys.stdout if output == "stdout" else sys.stderr
            op_stream.write(formatted_stats)
        else:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(formatted_stats)
    
    def _formatStats(self, stats_data):

        lines = [
            "--- REDACTION STATS ---",
            f"Created on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n--- Summary ---"
        ]

        for cat, data in stats_data['summary'].items():
            lines.extend([
                f"\n{cat.upper()}:",
                f"Total unique items: {data['count']}",
                f"Items:" if data['items'] else "No items found",
                "\n".join(f" - {item}" for item in data['items'])
            ])
        lines.append("\n --- File Details ---")
        for filename, file_data in stats_data['files'].items():
            lines.extend([
                "\nFile: {filename}",
                f"Total characters: {file_data['total_chars']}",
                f"Total redactions: {file_data['total_redaction']}",
                "\nRedacted items:"
            ])
        
        for item in file_data['redacted_items']:
            lines.append(
                f" - [{item['category']}] {item['text']} "
                f"(indices: {item['start_index']}-{item['end_index']})"
            )
        
        return "\n".join(lines)
    
    

class TextRedactor:
    def __init__(self, model_name: str = "en_core_web_md"):
        self.nlp = spacy.load(model_name)
        self.stats = RedactionStats()
        self._setup_extensions()
        self._register_pipeline_components()
        self._setup_pipeline()
        self.concepts = set()
    
    def _add_redacted_items(self, doc, text, start, end, category):

        if doc._.file_stats is None:
            return
        
        item = RedactionItem(
            text = text,
            start_idx=start,
            end_idx=end,
            category=category
        )

        doc._.file_stats.redacted_items.append(item)
        doc._.file_stats.total_redaction += 1

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
        if not spacy.tokens.Doc.has_extension("file_stats"):
            spacy.tokens.Doc.set_extension("file_stats", default=None)

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
                    self._add_redacted_items(doc, ent.text, ent.start_char, ent.end_char, "NAME")


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
                    self._add_redacted_items(doc, ent.text, ent.start_char, ent.end_char, "NAME")


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
                    self._add_redacted_items(doc, ent.text, ent.start_char, ent.end_char, "DATE")


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
                    self._add_redacted_items(doc, ent.text, ent.start_char, ent.end_char, "ADDRESS")


            doc._.redacted_text = TextRedactor._apply_redaction(redacted_text, spans_to_redact)
            doc._.redaction_spans.extend(spans_to_redact)
            return doc

        @Language.component("redact_concepts")
        def redact_concepts(doc):
            redacted_text = doc._.redacted_text
            spans_to_redact = []
            stats = doc._.stats
            concepts = doc._.concepts

            nltk_words = nltk.word_tokenize(" ".join(concepts))
            synonyms = {}
            for w in nltk_words:
                synonyms[w] = set()
                for synset in wordnet.synsets(w):
                    for lemma in synset.lemmas():
                        synonyms[w].add(lemma.name())
            
            #redact synonys relate to the concepts
            if synonyms:
                for key, span in synonyms.items():
                    for syn in span:
                        for match in re.finditer(syn, redacted_text):
                            spans_to_redact.append((match.start(), match.end()))
                            stats.concepts.add(match.group())


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

    def redact_text(self, text: str, filename: str = "default", concepts: List[str] = None) -> str:
        """Main method to redact text"""
        # Initialize document extensions
        doc = self.nlp.make_doc(text)
        doc._.redacted_text = text
        doc._.stats = self.stats# Initialize with a new RedactionStats object
        doc._.concepts = set(concepts) if concepts else set()

        file_stats = FileStats(
            filename=filename,
            total_ch = len(text),
            total_redaction=0
        )

        doc._.file_stats = file_stats
        self.stats.file_stats[filename] = file_stats
        
        # Process through pipeline
        doc = self.nlp(doc)  # Pass the doc object instead of text
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
        redacted_text = redactor.redact_text(
            text, 
            filename=os.path.basename(input_file), 
            concepts = args.concept)
        
        # Write output
        output_path = os.path.join(args.output, os.path.basename(input_file) + '.censored')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(redacted_text)
    
    # Write stats if requested
    if args.stats:
        redactor.stats.write_stats(args.stats)

if __name__ == "__main__":
    main()