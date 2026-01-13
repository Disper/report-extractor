# PDF Text Extractor

A simple Python application that extracts text from PDF files using pdfminer.six. By default, it extracts text from pages 2 and 3.

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
Extract text from pages 2 and 3 of `raport.pdf` and save to `raport_extracted.txt`:
```bash
python extract_text.py
```

### Custom Input/Output/Pages
Extract text from a custom PDF file and pages:
```bash
python extract_text.py input.pdf output.txt "2 3"
# or with comma-separated pages
python extract_text.py input.pdf output.txt "2,3"
```

### Command Line Arguments
- First argument: Path to PDF file (default: `raport.pdf`)
- Second argument: Path to output text file (default: `raport_extracted.txt`)
- Third argument: Page numbers to extract, space or comma-separated (1-indexed, default: `2 3`)

## Example

```bash
# Extract pages 2 and 3 from raport.pdf (default)
python extract_text.py

# Extract pages 2 and 3 from a different PDF
python extract_text.py document.pdf extracted_text.txt

# Extract different pages (e.g., pages 1 and 2)
python extract_text.py raport.pdf output.txt "1 2"

# Extract a single page (e.g., page 1)
python extract_text.py raport.pdf output.txt 1
```

## Requirements

- Python 3.6+
- pdfminer.six
