import fitz  # PyMuPDF
import json
import jsonschema
from pathlib import Path
import re
import datetime
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import multiprocessing
import os

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_SECTION_LENGTH = 512

def is_valid_heading(text):
    if not text:
        return False
    text = text.strip()
    if len(text) < 4:
        return False
    exclude_headings = {"table of contents", "references", "bibliography", "appendix"}
    if text.lower() in exclude_headings:
        return False
    if re.match(r'^[\W_]+$', text):
        return False
    return True

def extract_title(doc):
    title = doc.metadata.get("title", "").strip()
    if title:
        return title
    first_page_text = doc[0].get_text("text").strip()
    lines = [l.strip() for l in first_page_text.splitlines() if l.strip()]
    return lines[0] if lines else "Untitled Document"

def extract_outline(doc):
    toc = doc.get_toc()
    outline = []
    if toc:
        seen = set()
        for lvl, text, page in toc:
            text = text.strip()
            if not is_valid_heading(text):
                continue
            key = (lvl, text, page)
            if key in seen:
                continue
            seen.add(key)
            outline.append({"level": f"H{int(lvl)}" if str(lvl).isdigit() else str(lvl),
                            "text": text,
                            "page": page})
        return outline
    # Fallback to heuristic extraction
    heading_patterns = [
        r'^(?:[0-9]+\.?)+\s+[A-Z][^\n]{3,}',
        r'^[A-Z][A-Z ]{4,}$',
        r'^[A-Z][^\n]{4,}$'
    ]
    heading_re = re.compile("|".join(heading_patterns))
    found_headings = set()
    max_font_overall = 0
    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        max_font = 0
        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    size = span.get("size", 0)
                    if size > max_font:
                        max_font = size
        max_font_overall = max(max_font_overall, max_font)
        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if (not text) or (text in found_headings):
                        continue
                    font_size = span.get("size", 0)
                    if (font_size >= max_font - 3 or heading_re.match(text)) and is_valid_heading(text):
                        found_headings.add(text)
                        level = "H1" if font_size >= max_font_overall - 1 else "H2"
                        outline.append({"level": level, "text": text, "page": page_num})
    return outline

def segment_text_by_headings(doc):
    sections = []
    outline = extract_outline(doc)
    if not outline:
        full_text = ""
        for page in doc:
            full_text += page.get_text("text") + "\n"
        sections.append({"title": doc.metadata.get("title", "Untitled"), "text": full_text, "page": 1})
        return sections
    for i, heading in enumerate(outline):
        start_page = heading["page"]
        end_page = outline[i+1]["page"] - 1 if i+1 < len(outline) else doc.page_count
        text = ""
        for p in range(start_page - 1, end_page):
            text += doc[p].get_text("text") + "\n"
        sections.append({"title": heading["text"], "text": text.strip(), "page": start_page})
    return sections

def truncate_text(text, max_length=512):
    words = text.split()
    if len(words) > max_length:
        return " ".join(words[:max_length])
    return text

def embed_texts(model, texts):
    truncated_texts = [truncate_text(t, MAX_SECTION_LENGTH) for t in texts]
    embeddings = model.encode(truncated_texts, convert_to_numpy=True, batch_size=8)
    return embeddings

def process_single_document(args):
    pdf_path, persona_job_text, model, schema = args
    doc = fitz.open(pdf_path)
    sections = segment_text_by_headings(doc)
    persona_emb = model.encode([persona_job_text], convert_to_numpy=True)[0]
    section_texts = [sec["text"] for sec in sections]
    section_embs = embed_texts(model, section_texts)
    sims = cosine_similarity([persona_emb], section_embs)[0]
    ranked = sorted(
        [
            {
                "section": sec,
                "score": sim,
                "importance_rank": rank + 1
            }
            for rank, (sec, sim) in enumerate(sorted(zip(sections, sims), key=lambda x: x[1], reverse=True))
        ],
        key=lambda x: x["importance_rank"]
    )
    extracted_sections = []
    sub_section_analysis = []
    for r in ranked:
        sec = r["section"]
        refined_text = truncate_text(sec["text"], max_length=300)
        extracted_sections.append({
            "document": pdf_path.name,
            "page_number": sec["page"],
            "section_title": sec["title"],
            "importance_rank": r["importance_rank"]
        })
        sub_section_analysis.append({
            "document": pdf_path.name,
            "refined_text": refined_text,
            "page_number": sec["page"]
        })
    output = {
        "metadata": {
            "input_documents": [pdf_path.name],
            "persona": persona_job_text,
            "job_to_be_done": persona_job_text,
            "processing_timestamp": datetime.datetime.utcnow().isoformat()
        },
        "extracted_sections": extracted_sections,
        "sub_section_analysis": sub_section_analysis
    }
    jsonschema.validate(instance=output, schema=schema)
    return pdf_path.name, output

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Process PDF collection for persona-driven document intelligence.")
    parser.add_argument("--input_dir", type=str, default="/app/input", help="Input directory with PDFs")
    parser.add_argument("--output_dir", type=str, default="/app/output", help="Output directory for JSON")
    parser.add_argument("--persona_file", type=str, default="/app/persona_job.txt", help="File with persona and job description")
    parser.add_argument("--schema_path", type=str, default="/app/schema/challenge1b_output_schema.json", help="JSON schema")

    args = parser.parse_args()

    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(list(input_path.glob("*.pdf")))
    print(f"Found {len(pdf_files)} PDF file(s) in {input_path}:")
    for pdf in pdf_files:
        print(" -", pdf.name)
    if not pdf_files:
        print(f"No PDF files found in input directory {input_path}")
        return

    with open(args.persona_file, "r", encoding="utf-8") as f:
        persona_job_text = f.read().strip()
    with open(args.schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    model = SentenceTransformer(MODEL_NAME)

    task_args = [(pdf, persona_job_text, model, schema) for pdf in pdf_files]
    results = []
    for pdf_name, result_json in map(process_single_document, task_args):
        results.append((pdf_name, result_json))
        out_file = output_path / f"{Path(pdf_name).stem}.json"
        with open(out_file, "w", encoding="utf-8") as out_f:
            json.dump(result_json, out_f, indent=2, ensure_ascii=False)
        print(f"[OK] Processed {pdf_name}, output saved to {out_file}")
    print(f"Processing complete for {len(results)} document(s).")

if __name__ == "__main__":
    main()
