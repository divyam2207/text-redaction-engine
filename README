# cis6930fa24 -- Project 0 

Name: Divyam Dubey


# Project Description
This project implements a text redaction pipeline that automates the process of identifying and censoring sensitive information from text documents. It utilizes a command-line interface to enable users to specify the types of sensitive data they wish to redact, making it flexible for various use cases, such as processing police reports, court transcripts, and hospital records.

We are using the  full block character █ (U+2588) to redact the words based on our parameters. And we are using SPACY's doc object entities to span the word length, based on that we are not redacting the whitespaces, while for concept redaction, nltk redacts the spaces between words as well. The white space redaction is required to achieve complete abstraction, not letting even the context of redacted words be leaked out.

Concept is recognized in the files as a simple SPACY word match, case in-sensitive matching, followed by NLTK's advanced synonym search, which redacts any synonym search present in the file to hide the similar words as well.

This project uses Python3 to implement functions that:
1. Run throught the current directory, scans each file with the input extension
2. Perform redaction based on the input arguments using spaCy, regular expression, and NLTK wordnet synonym matching.
3. Followed by storing the redacted files with name--> {existing_name<dot>extension}<dot>censored.
4. Saves and prints out the statistics of the program to the given format in the input argument.

**Libraries Used**:
- *spacy*: For natural language processing and named entity recognition
- *nltk*: For advanced concept redaction and synonym detection
- *argparse*: For command-line argument parsing
- *datetime*: For timestamp generation in reports
- *re*: For pattern matching
- *typing*: For type hints
- *dataclasses*: For data structure organization

# How to Install
Run the following to install the required dependencies:

1. Download python virtual environment
```bash
pipenv install
```

2. Install spacy and nltk libraries:

```bash
pip install nltk
pip install spacy
```
3. Download spacy's large model for refined redaction:

```bash
python -m spacy download en_core_web_lg
```
4. Import NLTK and download the wordnet and omw data
```bash
import nltk
nltk.download("omw-1.4")
nltk.download("wordnet")
```

# How to run
```
pipenv run python redactor.py --input {file_extension} --names --dates --phones --address --concept {concept word: str} --output '{file_location}' --stats {stream_type}
```
## Example:
```
python redactor.py --input "*.txt" --names --dates --phones --address --concept "secret" --output ./redacted --stats stderr
```


## Stats Output format
```bash
--- REDACTION STATS ---
Created on: 2024-10-31 12:00:00

--- Summary ---
NAMES:
Total unique items: 10
Items:
 - John Doe
 - Jane Smith
...

--- File Details ---
File: example.txt
Total characters: 1000
Total redactions: 15
Redacted items:
 - [NAME] John Doe (indices: 10-18)
 - [DATE] 2024-10-31 (indices: 20-30)
```


## Command Line Arguments
- --input: Input file pattern (e.g., "*.txt")
- --names: Enable name redaction
- --dates: Enable date redaction
- --phones: Enable phone number redaction
- --address: Enable address redaction
- --concept: Concepts to redact (can be specified multiple times)
- --output: Output directory for redacted files
- --stats: Output file for redaction statistics

## Code Components

### Classes

#### `RedactionItem`
Represents a single redaction item with text, start and end indices, and category.

- **Attributes:**
  - `text` (str): Redacted text content.
  - `start_idx` (int): Start index of redaction.
  - `end_idx` (int): End index of redaction.
  - `category` (str): Category of redaction (e.g., "NAME").

---

#### `FileStats`
Stores file statistics.

- **Attributes:**
  - `filename` (str): File name.
  - `size` (int): File size in bytes.
  - `num_redactions` (int): Number of redactions made.

---

### Functions

#### `redact_text(text: str, redaction_items: List[RedactionItem]) -> str`
Redacts specified items from the given text.

- **Parameters:**
  - `text` (str): Original text.
  - `redaction_items` (List[RedactionItem]): Items to redact.

- **Returns:**  
  - `str`: Redacted text.

---

#### `calculate_file_stats(filepath: str) -> FileStats`
Calculates statistics for the given file.

- **Parameters:**
  - `filepath` (str): Path to the file.

- **Returns:**  
  - `FileStats`: Statistics of the file.

---

#### `log_redactions(file_stats: FileStats)`
Logs redaction statistics.

- **Parameters:**
  - `file_stats` (FileStats): File statistics to log.

### Tests Overview

## `test_names.py`

## `test_redact_names()`
Tests redaction of personal names from a text sample.
- **Input:** Text containing a personal name.
- **Expected Outcome:** Names are redacted, matching the expected redaction format.

---
## `test_dates.py`

## `test_redact_dates()`
Tests redaction of dates from a text sample.
- **Input:** Text containing a date.
- **Expected Outcome:** Date is redacted, matching the expected redaction format. Additionally, the original date appears in `stats.dates`.


## `test_address.py`

### `test_redact_addresses()`
Tests redaction of address-related information from a text sample.
- **Input:** Text containing an address.
- **Expected Outcome:** Address is redacted, with redaction recorded in `stats.addresses`.

---

## `test_concepts.py`

### `test_redact_concepts()`
Tests redaction of specified concept keywords from a text sample.
- **Input:** Text containing specified concepts.
- **Expected Outcome:** Concepts are redacted, with redactions recorded in `stats.concepts`.

---

## `test_phones.py`

### `test_redact_phones()`
Tests redaction of phone numbers from a text sample.
- **Input:** Text containing phone numbers.
- **Expected Outcome:** Phone numbers are redacted, with redaction recorded in `stats.phones`.

## Running the Tests
To run the tests, use the following command:

```bash
pipenv run python -m pytest
```

## Bugs and Assumptions

- Requires SpaCy's large English model for optimal performance, getting better performance on large spacy model than smaller ones.
- Pattern-based redaction may have false positives, since email name, address, phones could be written in odd format.
- Some 10 digit numbers such as ID etc. are being redacted by the program, mis judging it as a phone number.
- Custom concept redaction depends on WordNet coverage
- All input files are assumed to be UTF-8 encoded
- Memory usage scales with input file size
