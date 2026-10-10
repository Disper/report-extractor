#!/usr/bin/env python3
"""
PDF Text Extractor using pdfminer.six
Extracts text from the second and third pages of raport.pdf and saves it to a text file.
"""

from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import sys
import os
import json
import re


def extract_pdf_text(pdf_path, output_path=None, page_numbers=[2, 3]):
    """
    Extract text from a PDF file using pdfminer.six
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Optional path to save the extracted text. 
                     If None, prints to stdout.
        page_numbers: List of page numbers to extract (1-indexed). Default is [2, 3].
    
    Returns:
        Extracted text as a string
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Configure layout parameters for better text extraction
    laparams = LAParams(
        line_margin=0.5,
        word_margin=0.1,
        char_margin=2.0,
        boxes_flow=0.5,
        all_texts=False
    )
    
    try:
        # Extract text from specific pages (page_numbers are 1-indexed, convert to 0-indexed)
        # page_numbers parameter expects 0-indexed page numbers
        page_indices = [page_num - 1 for page_num in page_numbers]
        text = extract_text(pdf_path, laparams=laparams, page_numbers=page_indices)
        
        if output_path:
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            pages_str = ", ".join(map(str, page_numbers))
            print(f"Text extracted successfully from pages {pages_str} to: {output_path}")
            print(f"Total characters extracted: {len(text)}")
        else:
            # Print to stdout
            print(text)
        
        return text
    
    except Exception as e:
        print(f"Error extracting text from PDF: {e}", file=sys.stderr)
        raise


def extract_values_from_text(text, page_numbers=[2, 3]):
    """
    Extract specific values from extracted PDF text.
    
    Args:
        text: Extracted text from PDF
        page_numbers: List of page numbers that were extracted (for labeling)
    
    Returns:
        Dictionary with page numbers as keys and extracted values as nested dictionaries
    """
    # Split text by form feed characters to separate pages
    pages = text.split('\f')
    
    # Remove empty pages
    pages = [page.strip() for page in pages if page.strip()]
    
    # Pattern to match monetary values (e.g., "1 278,60 zł", "20,00 zł")
    monetary_pattern = re.compile(r'\d+[\s\d]*,\d+\s*zł')
    
    results = {}
    
    for idx, page_text in enumerate(pages):
        if idx >= len(page_numbers):
            break
        
        page_num = page_numbers[idx]
        page_key = f"page_{page_num}"
        page_results = {}
        
        # All monetary values before the utilities table, in document order:
        # A(0) B(1-5) C(6-10) pozostale(11) D(12) E(13) F(14) F_sub(15) ?(16) G(17).
        # Extra description lines (e.g. "(Usługa remontowa, ...)") contain no
        # amounts, so the order is stable regardless of the values themselves.
        payment_pos = page_text.find("Płatności z tyt. opłat eksploatacyjnych lokalu")
        body = page_text if payment_pos < 0 else page_text[:payment_pos]
        amount_pattern = re.compile(r'^\s*(\d{1,3}(?:[ \u00a0]\d{3})*,\d{2}\s*zł)\s*$', re.M)
        values = amount_pattern.findall(body)

        c_wydatki_value = e_value = f_value = pozostale_wydatki_value = None
        if len(values) == 18:
            c_wydatki_value = values[6]
            pozostale_wydatki_value = values[11]
            e_value = values[13]
            f_value = values[14]

            def num(v):
                return float(v.replace("zł", "").replace(" ", "").replace("\xa0", "").replace(",", "."))

            a_, b_, c_, e_, f_, g_ = (num(values[i]) for i in (0, 1, 6, 13, 14, 17))
            if abs(a_ + b_ - c_ - e_ - f_ - g_) > 0.005:
                print(f"WARNING: {page_key}: A+B-C-E-F != G, check values", file=sys.stderr)
        else:
            print(f"WARNING: {page_key}: expected 18 amounts, found {len(values)}", file=sys.stderr)

        page_results["C_WYDATKI_OGOLEM"] = c_wydatki_value if c_wydatki_value else None
        page_results["E_PRZELEW_DO_WLASCICIELA"] = e_value if e_value else None
        page_results["F_WYDATKI_Z_SALDA"] = f_value if f_value else None
        page_results["POZOSTALE_WYDATKI"] = pozostale_wydatki_value if pozostale_wydatki_value else None
        results[page_key] = page_results
    
    return results


def main():
    """Main function to run the text extraction"""
    pdf_file = "raport.pdf"
    output_file = "raport_extracted.txt"
    page_numbers = [2, 3]  # Extract pages 2 and 3
    
    # Check if custom paths provided via command line
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        # Parse page numbers from command line (comma-separated or space-separated)
        page_input = sys.argv[3]
        if ',' in page_input:
            page_numbers = [int(p.strip()) for p in page_input.split(',')]
        else:
            page_numbers = [int(p) for p in page_input.split()]
    
    pages_str = ", ".join(map(str, page_numbers))
    print(f"Extracting text from pages {pages_str} of: {pdf_file}")
    extracted_text = extract_pdf_text(pdf_file, output_file, page_numbers)
    
    # Extract specific values from the text
    print("Extracting specific values from the text...")
    extracted_values = extract_values_from_text(extracted_text, page_numbers)
    
    # Generate output filename from PDF filename: [name]_output.json
    pdf_basename = os.path.splitext(os.path.basename(pdf_file))[0]
    output_values_file = f"{pdf_basename}_output.json"
    
    # Save extracted values to output file
    with open(output_values_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_values, f, ensure_ascii=False, indent=2)
    
    print(f"Extracted values saved to: {output_values_file}")
    for page_key, values in extracted_values.items():
        print(f"  {page_key}:")
        for key, value in values.items():
            print(f"    {key}: {value}")
    
    # Create formula file with two rows
    formula_file = f"{pdf_basename}_formulas.txt"
    
    # Get values from extracted data and format for formulas
    def format_for_formula(value):
        """Remove ' zł' suffix, replace comma with dot, and remove spaces"""
        if not value:
            return value
        # Remove " zł" suffix if present
        if value.endswith(" zł"):
            value = value[:-3].strip()
        # Replace comma with dot for decimal separator
        value = value.replace(",", ".")
        # Remove all spaces
        value = value.replace(" ", "")
        return value
    
    page_2_e = format_for_formula(extracted_values.get("page_2", {}).get("E_PRZELEW_DO_WLASCICIELA", ""))
    page_3_e = format_for_formula(extracted_values.get("page_3", {}).get("E_PRZELEW_DO_WLASCICIELA", ""))
    page_2_c = format_for_formula(extracted_values.get("page_2", {}).get("C_WYDATKI_OGOLEM", ""))
    page_2_pozostale = format_for_formula(extracted_values.get("page_2", {}).get("POZOSTALE_WYDATKI", ""))
    page_2_f = format_for_formula(extracted_values.get("page_2", {}).get("F_WYDATKI_Z_SALDA", ""))
    page_3_c = format_for_formula(extracted_values.get("page_3", {}).get("C_WYDATKI_OGOLEM", ""))
    page_3_pozostale = format_for_formula(extracted_values.get("page_3", {}).get("POZOSTALE_WYDATKI", ""))
    page_3_f = format_for_formula(extracted_values.get("page_3", {}).get("F_WYDATKI_Z_SALDA", ""))

    # Create the two formula rows
    row1 = f"={page_2_e}+{page_3_e}"
    row2 = f"={page_2_c}+{page_2_f}+{page_3_c}+{page_3_f}"
    
    # Write to file
    with open(formula_file, 'w', encoding='utf-8') as f:
        f.write(row1 + '\n')
        f.write(row2 + '\n')
    
    print(f"Formula file created: {formula_file}")


if __name__ == "__main__":
    main()
