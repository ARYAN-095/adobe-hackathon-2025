import fitz  # PyMuPDF
import json
import os
import re
import statistics
from collections import defaultdict
import argparse

def get_document_styles(doc):
    """
    Determines the most common font size in the document, likely the body text size.
    Args:
        doc: The PyMuPDF document object.
    Returns:
        The most frequent font size (rounded).
    """
    font_sizes = defaultdict(int)
    # Analyze a subset of pages for efficiency on very large documents
    pages_to_scan = min(len(doc), 20)
    for i in range(pages_to_scan):
        page = doc[i]
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes[round(span["size"])] += len(span["text"])
    if not font_sizes:
        return 12 # Default if no text is found
    return max(font_sizes, key=font_sizes.get)

def get_repetitive_lines(doc):
    """
    Identifies lines that are likely headers or footers by checking for repetition.
    Args:
        doc: The PyMuPDF document object.
    Returns:
        A set of repetitive text lines.
    """
    line_count = defaultdict(int)
    total_pages = len(doc)
    if total_pages < 3: # Don't run on very short documents
        return set()

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()
        lines = text.split('\n')
        # Check top and bottom 5 lines for headers/footers
        for line in lines[:5] + lines[-5:]:
            cleaned_line = line.strip()
            # Ignore page numbers and very short lines
            if len(cleaned_line) > 5 and not cleaned_line.isdigit():
                line_count[cleaned_line] += 1
    
    # A line is repetitive if it appears on more than 70% of pages
    return {line for line, count in line_count.items() if count >= total_pages * 0.7}

def extract_outline(pdf_path):
    """
    Main function to extract the title and a structured outline from a PDF.
    This version uses a rule-based approach for identifying numbered headings.
    Args:
        pdf_path: Path to the PDF file.
    Returns:
        A dictionary containing the title and the outline.
    """
    doc = fitz.open(pdf_path)
    body_text_size = get_document_styles(doc)
    repetitive_lines = get_repetitive_lines(doc)
    outline = []
    title = ""

    # --- Title Detection (First Page) ---
    first_page = doc[0]
    blocks = first_page.get_text("dict", sort=True)["blocks"]
    # Find the largest font size on the first page
    max_font_size = 0
    for block in blocks:
        for line in block.get("lines", []):
            for span in line["spans"]:
                 if span['size'] > max_font_size:
                    max_font_size = span['size']
    
    # Concatenate all text with the largest font size to form the title
    title_parts = []
    for block in blocks:
        for line in block.get("lines", []):
            for span in line["spans"]:
                if round(span['size']) == round(max_font_size):
                    title_parts.append(span['text'].strip())
    title = " ".join(title_parts).strip()


    # --- Heading Detection (All Pages) ---
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict", sort=True)["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                if not line["spans"]:
                    continue

                # Combine spans to get the full line text and its primary font size
                full_text = "".join(s["text"] for s in line["spans"]).strip()
                primary_font_size = line["spans"][0]["size"]
                is_bold = "bold" in line["spans"][0]["font"].lower()

                if not full_text or full_text in repetitive_lines or full_text.lower() == title.lower():
                    continue

                # Rule 1: Numbered Headings (e.g., "1.", "2.1", "3.1.4")
                match = re.match(r'^(\d+(\.\d+)*)\s+(.*)', full_text)
                if match:
                    numbering = match.group(1)
                    level = len(numbering.split('.'))
                    
                    # Add to outline if it's not a tiny font size
                    if primary_font_size > body_text_size * 0.9:
                         outline.append({
                            "level": f"H{level}",
                            "text": full_text,
                            "page": page_num + 1
                        })
                    continue # Move to the next line once matched

                # Rule 2: Non-numbered headings (e.g., "Acknowledgements", "Table of Contents")
                # These are usually short, bold, and have a larger font size.
                is_short = len(full_text.split()) < 5
                is_significantly_larger = primary_font_size > body_text_size * 1.15
                
                if is_short and is_significantly_larger and is_bold:
                    # Avoid adding lines that are part of the title again
                    if full_text not in title:
                        outline.append({
                            "level": "H1",
                            "text": full_text,
                            "page": page_num + 1
                        })

    # --- Post-processing: Remove duplicate headings on the same page ---
    final_outline = []
    seen = set()
    for item in outline:
        identifier = (item['text'], item['page'])
        if identifier not in seen:
            final_outline.append(item)
            seen.add(identifier)

    return {"title": title, "outline": final_outline}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract a structured outline from all PDF files in a directory.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--input_dir",
        default="input",
        help="Directory containing the PDF files to process."
    )
    parser.add_argument(
        "--output_dir",
        default="output",
        help="Directory where the output JSON files will be saved."
    )
    args = parser.parse_args()

    INPUT_DIR = args.input_dir
    OUTPUT_DIR = args.output_dir

    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"Searching for PDF files in: {os.path.abspath(INPUT_DIR)}")

    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"No PDF files found in '{INPUT_DIR}'. Please add files and retry.")
    else:
        for filename in pdf_files:
            try:
                pdf_path = os.path.join(INPUT_DIR, filename)
                print(f"Processing {filename}...")
                
                output_data = extract_outline(pdf_path)

                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(OUTPUT_DIR, output_filename)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)

                print(f"✓ Successfully processed {filename}. Output saved to {output_path}")

            except Exception as e:
                print(f"✗ Error processing {filename}: {e}")
