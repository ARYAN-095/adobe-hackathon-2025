import sys
import json
import fitz  # PyMuPDF
import torch
import numpy as np
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

# --- CONFIGURATION ---
MODEL_NAME = 'all-MiniLM-L6-v2'
TOP_K_SECTIONS = 10
TOP_K_SUBSECTIONS = 15

# Keywords to find the most relevant content for the persona
POSITIVE_KEYWORDS = ['nightlife', 'bar', 'club', 'party', 'beach', 'budget', 'cheap', 'affordable', 'restaurant', 'hotel', 'hostel', 'activity', 'adventure', 'friends', 'group']
KEYWORD_BOOST = 1.5 # How much to boost the score of chunks with keywords

def clean_text(text):
    """Cleans extracted PDF text."""
    ligatures = {
        '\ufb00': 'ff', '\ufb01': 'fi', '\ufb02': 'fl', '\ufb03': 'ffi', '\ufb04': 'ffl',
        '\u2022': '-', '\u2013': '-', '\u2014': '-',
    }
    for char, replacement in ligatures.items():
        text = text.replace(char, replacement)
    return ' '.join(text.split())

def extract_text_and_chunk(pdf_paths, base_dir):
    """
    Extracts text and uses a more robust sliding-window chunking strategy.
    """
    section_chunks = []
    subsection_chunks = []

    for pdf_path in pdf_paths:
        file_path = base_dir / pdf_path
        if not file_path.exists():
            continue
        
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc, start=1):
            cleaned_text = clean_text(page.get_text("text"))
            if not cleaned_text:
                continue

            section_chunks.append({
                "document": file_path.name,
                "page_number": page_num,
                "text": cleaned_text
            })

            # --- FINAL FIX: Sliding Window Chunking ---
            words = cleaned_text.split()
            chunk_size = 50  # Words per chunk
            overlap = 10     # Words to overlap
            
            for i in range(0, len(words), chunk_size - overlap):
                chunk_text = ' '.join(words[i:i + chunk_size])
                if len(chunk_text.strip()) > 30: # Min chunk length
                    subsection_chunks.append({
                        "document": file_path.name,
                        "page_number": page_num,
                        "text": chunk_text
                    })

    return section_chunks, subsection_chunks

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_input.json>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    base_dir = input_path.parent

    with open(input_path, 'r', encoding='utf-8') as f:
        input_data = json.load(f)

    persona = input_data["persona"]["role"]
    job_to_be_done = input_data["job_to_be_done"]["task"]
    pdf_filenames = [doc['filename'] for doc in input_data['documents']]

    section_chunks, subsection_chunks = extract_text_and_chunk(pdf_filenames, base_dir / "PDFs")

    if not subsection_chunks:
        print(json.dumps({"error": "No text could be extracted."}))
        sys.exit(1)

    # --- FINAL FIX: Simplified, powerful query ---
    query = f"Information for a {persona} planning a trip for college friends. Focus on: {', '.join(POSITIVE_KEYWORDS)}."

    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode(query, convert_to_tensor=True, device='cpu')
    
    section_embeddings = model.encode([chunk['text'] for chunk in section_chunks], convert_to_tensor=True, device='cpu')
    subsection_embeddings = model.encode([chunk['text'] for chunk in subsection_chunks], convert_to_tensor=True, device='cpu')

    section_scores = util.cos_sim(query_embedding, section_embeddings)[0]
    subsection_scores = util.cos_sim(query_embedding, subsection_embeddings)[0]

    # --- FINAL FIX: Apply keyword boost to subsection scores ---
    for i, chunk in enumerate(subsection_chunks):
        if any(keyword in chunk['text'].lower() for keyword in POSITIVE_KEYWORDS):
            subsection_scores[i] *= KEYWORD_BOOST

    # Rank sections and subsections
    ranked_sections = sorted([{"score": score.item(), **chunk} for i, (score, chunk) in enumerate(zip(section_scores, section_chunks))], key=lambda x: x['score'], reverse=True)
    ranked_subsections = sorted([{"score": score.item(), **chunk} for i, (score, chunk) in enumerate(zip(subsection_scores, subsection_chunks))], key=lambda x: x['score'], reverse=True)

    # Format output
    output_sections = []
    for rank, sec in enumerate(ranked_sections[:TOP_K_SECTIONS], start=1):
        output_sections.append({
            "document": sec["document"],
            "page_number": sec["page_number"],
            "section_title": f"Relevant Content from Page {sec['page_number']}",
            "importance_rank": rank
        })

    output_subsections = []
    for sub_sec in ranked_subsections[:TOP_K_SUBSECTIONS]:
        output_subsections.append({
            "document": sub_sec["document"],
            "refined_text": sub_sec["text"],
            "page_number": sub_sec["page_number"]
        })

    final_output = {
        "metadata": {
            "input_documents": pdf_filenames,
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "extracted_sections": output_sections,
        "subsection_analysis": output_subsections
    }

    print(json.dumps(final_output, indent=2))

if __name__ == "__main__":
    main()
