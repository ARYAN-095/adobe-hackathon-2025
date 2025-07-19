import fitz  # PyMuPDF
import json
import os
import re
import statistics
from collections import defaultdict

def get_document_styles(doc):
    font_sizes = defaultdict(int)
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes[round(span["size"])] += len(span["text"])
    return max(font_sizes, key=font_sizes.get, default=12)

def get_page_font_stats(page):
    sizes = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                sizes.append(span["size"])
    if not sizes:
        return 12, 12
    return statistics.mean(sizes), max(sizes)

def get_repetitive_lines(doc):
    line_count = defaultdict(int)
    total_pages = len(doc)

    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = "".join(span["text"] for span in line["spans"]).strip()
                if text:
                    line_count[text] += 1

    return {line for line, count in line_count.items() if count >= total_pages * 0.9}

def score_line(line, body_text_size, page_mean, page_max):
    if not line['spans']:
        return 0, ""

    span = line['spans'][0]
    text = span['text'].strip()
    if not text:
        return 0, ""

    score = 0

    # 1. Font Size Relative to Document Body
    score += (span['size'] / body_text_size - 1) * 10

    # 2. Font Size Relative to Page
    score += (span['size'] / page_mean - 1) * 5

    # 3. Bold Font
    if "bold" in span['font'].lower():
        score += 5

    # 4. All Caps
    if text.isupper() and len(text) > 3:
        score += 3

    # 5. Brevity
    if len(text.split()) < 10:
        score += 3

    # 6. Heading Number Pattern (e.g., 1.2.3.)
    if re.match(r'^(\d+[\.\d]*)\s+', text):
        score += 3

    # 7. Penalty: likely sentence
    if text.endswith('.'):
        score -= 10

    return score, text

def extract_outline(pdf_path, body_text_size):
    doc = fitz.open(pdf_path)
    outline = []
    repetitive_lines = get_repetitive_lines(doc)

    # Title Detection from first page
    title = ""
    max_score = -1
    first_page_mean, _ = get_page_font_stats(doc[0])

    for block in doc[0].get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            score, text = score_line(line, body_text_size, first_page_mean, body_text_size)
            if score > max_score and text not in repetitive_lines:
                max_score = score
                title = text

    heading_candidates = []

    for page_num, page in enumerate(doc):
        page_mean, page_max = get_page_font_stats(page)
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                score, text = score_line(line, body_text_size, page_mean, page_max)
                if score > 5 and text not in repetitive_lines:
                    heading_candidates.append({
                        "score": score,
                        "text": text,
                        "page": page_num + 1
                    })

    if not heading_candidates:
        return {"title": title, "outline": []}

    scores = [h['score'] for h in heading_candidates]
    h1_threshold = statistics.quantiles(scores, n=4)[-1]  # top 25%
    h2_threshold = statistics.quantiles(scores, n=4)[1]   # middle 50%

    for h in heading_candidates:
        if h['score'] >= h1_threshold:
            level = "H1"
        elif h['score'] >= h2_threshold:
            level = "H2"
        else:
            level = "H3"
        outline.append({
            "level": level,
            "text": h["text"],
            "page": h["page"]
        })

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
                doc.close()

                output_data = extract_outline(pdf_path, body_size)

                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(OUTPUT_DIR, output_filename)

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)

                print(f"✓ Processed {filename}")

            except Exception as e:
                print(f"✗ Error processing {filename}: {e}")
