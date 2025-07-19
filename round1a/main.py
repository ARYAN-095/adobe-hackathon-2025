import fitz  # PyMuPDF
import json
import os
import statistics
from collections import defaultdict

def get_document_styles(doc):
    """
    Analyzes the entire document to find the most common font size and family,
    which we assume is the body text style.
    """
    font_sizes = defaultdict(int)
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes[round(span["size"])] += len(span["text"])
    
    if not font_sizes:
        return 12.0 # Default fallback
        
    # The size with the most characters is likely the body text
    body_text_size = max(font_sizes, key=font_sizes.get)
    return body_text_size

def score_line(line, body_text_size):
    """
    Scores a line based on multiple features to determine if it's a heading.
    This is the key to a robust solution.
    """
    if not line['spans']:
        return 0, ""

    span = line['spans'][0] # Assume single style for headings
    text = span['text'].strip()

    if not text:
        return 0, ""

    score = 0
    # 1. Font Size Score: Higher score for larger text relative to body
    score += (span['size'] / body_text_size - 1) * 10
    
    # 2. Boldness Score: A bold font is a strong indicator
    if "bold" in span['font'].lower():
        score += 5
        
    # 3. All Caps Score
    if text.isupper() and len(text) > 3:
        score += 3

    # 4. Brevity Score: Headings are usually short
    if len(text.split()) < 10:
        score += 3
        
    # 5. Penalty for ending with a period (likely a sentence)
    if text.endswith('.'):
        score -= 10
        
    return score, text

def extract_outline(pdf_path, body_text_size):
    doc = fitz.open(pdf_path)
    outline = []
    
    # Heuristic for Title: Often the line with the highest score on the first page
    title = ""
    max_score = -1
    for block in doc[0].get_text("dict")["blocks"]:
        if "lines" in block:
            for line in block["lines"]:
                score, text = score_line(line, body_text_size)
                if score > max_score:
                    max_score = score
                    title = text
    
    # Identify heading candidates based on score
    heading_candidates = []
    for page_num, page in enumerate(doc):
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    score, text = score_line(line, body_text_size)
                    # A threshold score to be considered a heading
                    if score > 5: # This threshold is key - tune it with sample docs
                        heading_candidates.append({'score': score, 'text': text, 'page': page_num + 1})

    # Classify candidates into H1, H2, H3 based on score distribution
    if not heading_candidates:
        return {"title": title, "outline": []}

    scores = [h['score'] for h in heading_candidates]
    # Use quantiles to create score boundaries for H1, H2, H3
    h1_threshold = statistics.quantiles(scores, n=4)[-1] # Top 25% scores are H1
    h2_threshold = statistics.quantiles(scores, n=4)[1] # Middle 50% scores are H2
    
    for h in heading_candidates:
        level = ""
        if h['score'] >= h1_threshold:
            level = "H1"
        elif h['score'] >= h2_threshold:
            level = "H2"
        else:
            level = "H3"
        outline.append({"level": level, "text": h['text'], "page": h['page']})
        
    return {"title": title, "outline": outline}

if __name__ == "__main__":
    INPUT_DIR = "/app/input"
    OUTPUT_DIR = "/app/output"

    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            try:
                pdf_path = os.path.join(INPUT_DIR, filename)
                doc = fitz.open(pdf_path)
                body_size = get_document_styles(doc)
                doc.close() # Close and reopen to be safe
                
                output_data = extract_outline(pdf_path, body_size)
                
                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Error processing {filename}: {e}")