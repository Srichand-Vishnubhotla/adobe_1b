Overview
This repository holds a solution for Round 1B: Persona-Driven Document Intelligence Challenge under the theme
"Connect What Matters — For the User Who Matters."
The goal is to create an intelligent document analysis system that extracts, ranks, and summarizes the most pertinent parts of a heterogeneous set of PDF documents according to a given persona and their job-to-be-done.

Our solution targets a wide range of document types such as research papers, business reports, educational texts, and can accommodate diverse personas including researchers, analysts, and students.

Solution Summary
Our system processes the following inputs:

A set of related PDF documents (3 to 10 documents).

A persona definition outlining the role, expertise, and focus areas.

A job-to-be-done describing a concrete task the persona desires to accomplish.

It produces a formatted JSON output containing:

Metadata about the inputs and processing timestamp.

Document sections extracted and ranked according to persona relevance.

Concise refined texts summarizing significant subsections.

Major Features and Strategy
Document Parsing & Section Extraction

Uses PyMuPDF (fitz) for fast and accurate text extraction along with document structure such as headings and page numbers.

Extracts document outlines (TOC) if available; otherwise, heuristically detects section headings by analyzing font sizes and text patterns.

Persona & Job-to-be-Done Embedding

Combines persona role description and job-to-be-done into a single contextual query.

Creates semantic embeddings from this combined query using a lightweight, CPU-efficient transformer model (sentence-transformers/all-MiniLM-L6-v2).

Section Embedding and Relevance Ranking

Converts document sections or subsections into dense vector representations through embedding.

Computes cosine similarity scores between section embeddings and the persona-job embedding.

Ranks sections by semantic relevance while incorporating importance heuristics such as section order and heading depth.

Text Refinement & Summarization

Generates brief yet informative refined texts for top-ranked sections.

Uses extractive summarization heuristics optimized for CPU-only environments.

Output Generation & Validation

Outputs JSON files conforming to the specified schema (challenge1b_output_schema.json).

Applies strict validation using jsonschema to ensure correctness of output.

Efficiency and Constraints

Entire solution is optimized for CPU-only execution, with all models quantized to remain within 1GB size limit.

Utilizes multiprocessing to maximize CPU utilization and completes processing within 60 seconds for typical document sets.

All models and dependencies are packaged inside a Docker image for offline execution with no internet access required during runtime.

Project Structure
text
project-root/
├── Dockerfile
├── requirements.txt
├── process_documents.py
├── persona_job.txt               # Persona and job-to-be-done text file
├── schema/
│   └── challenge1b_output_schema.json
├── input/                       # Place input PDF documents here
└── output/                      # JSON output files will appear here
Getting Started
Prerequisites
Docker installed on your system.

Input PDF documents for analysis.

A persona_job.txt file containing the concatenated persona and job-to-be-done description.

Build Docker Image
From the project root directory, run:

bash
docker build -t pdf-intel .
Run Container
Execute the container, mounting your local input and output folders:

bash
docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" pdf-intel
Note: On Windows Powershell, adjust the command accordingly:

powershell
docker run --rm -v "${PWD}/input:/app/input" -v "${PWD}/output:/app/output" pdf-intel
Outputs
For each input PDF, a corresponding JSON output file is generated inside the /output directory.

Each JSON includes metadata, prioritized sections with page numbers, and refined subsection texts aligned with the challenge's expected schema.

How It Works
The processor reads PDFs from /input.

Extracts sections based on document outline or heuristic heading detection.

Encodes the combined persona and job-to-be-done using a compact transformer model.

Embeds and scores each section for semantic similarity with the persona-job embedding.

Ranks sections accordingly.

Generates validated JSON outputs with ranked intelligent document insights.

Dependencies
Python 3.10

PyMuPDF 1.23.21

jsonschema 4.21.1

sentence-transformers 2.2.2 (compatible with huggingface-hub 0.10.1)

scikit-learn 1.2.2

numpy 1.24.3

All dependencies are pre-installed inside the Docker image for offline use.

Notes & Future Work
Currently uses simple extractive truncation for text refinement; future improvements may include lightweight abstractive summarization models.

Robust heading detection covers diverse document layouts but can be enhanced with domain-adaptive heuristics.

Designed for CPU-only environments; future upgrades can support GPU acceleration for speedup.

The JSON schema and persona/job definitions are configurable to support various document domains and tasks.
