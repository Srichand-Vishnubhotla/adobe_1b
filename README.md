Overview
This repository holds a solution for Round 1B: Persona-Driven Document Intelligence Challenge on the topic
"Connect What Matters — For the User Who Matters". The goal is to create an intelligent document analysis system that extracts, ranks, and summarizes the most pertinent parts of a set of heterogeneous PDF documents according to a given persona and his or her job-to-be-done.

Our solution is intended for varied document spaces like research papers, business reports, educational text, and accommodates varying personas from researchers to analysts and students.

Solution Summary
Our system processes as input:

A set of related PDF documents (3 to 10 documents),
A persona definition that outlines the job, expertise, and areas of interest,
A job-to-be-done—a real task the persona desires to get done.

The system generates a formatted JSON file with:

Metadata on the input and processing time,

Document sections extracted and ranked for the persona and the work,

Brief refined texts abridging significant subsections.

Major Features and Strategy
1. Document Parsing & Section Extraction
Leverages PyMuPDF (fitz) for quick, precise extraction of raw text with document organization like headings and page numbers.

Pulls out document outlines (TOC) when present; otherwise, heuristically finds section headings by scanning text font sizes and patterns.

2. Persona & Job-to-be-Done Embedding
Merges the persona role description and job-to-be-done text into one contextual query.

Translates this query into a semantic embedding from a lightweight, CPU-efficient transformer model: sentence-transformers/all-MiniLM-L6-v2.

3. Section Embedding and Relevance Ranking
Embeds document sections or subsections by translating their text into dense vector representations.

Calculates cosine similarity scores between each section embedding and the persona-job embedding.

Rank sections semantically relevant with importance heuristics such as section order and heading depth.

4. Text Refinement & Summarization
Delivers short but rich refined text for top-ranked sections.

Summarization adopts extractive heuristics appropriate for CPU-only scenarios.

5. Output Generation & Validation
Generates a JSON output according to the specified schema (challenge1b_output_schema.json).

Ensures strict schema validation using jsonschema to ensure correctness of output.

6. Efficiency and Constraints
Entire solution is optimized for CPU-only execution, with all models quantized to remain within a 1GB size constraint.

Uses multiprocessing to exhaustively use available CPU cores and completes the processing within 60 seconds for typical document sets.

All model and dependency are pre-packaged in a Docker image — no internet access at runtime needed.

Project Structure
text
project-root/
├── Dockerfile
├── requirements.txt
├── process_documents.py
├── persona_job.txt # Persona and job-to-be-done description text file
├── schema/
│ └── challenge1b_output_schema.json
├── input/ # Deposit input PDF documents here
└── output/ # Processed JSON outputs will appear here
Getting Started
Prerequisites
Docker installed on your system.

Input PDF documents for analysis.

Description file persona_job.txt containing the combined persona and job-to-be-done text.

Build Docker Image
From project root:

bash
docker build -t pdf-intel .
Run Container
bash
docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" pdf-intel
(On Windows Powershell, adjust path syntax accordingly.)

Outputs
The JSON files for each input PDF are found in the /output directory.

The JSON for each has metadata, prioritized sections with page numbers, and smoothed subsection texts matched against your challenge schema.

How It Works
The processor reads each PDF from /input.

Pulls sections based on outline or heuristics.

Immerses persona+job and sections with a compact transformer.

Ranks and scores sections semantically.
Scores and ranks the sections semantically.

Outputs validated JSON with ranked document intelligence.

Dependencies
Python 3.10

PyMuPDF 1.23.21

jsonschema 4.21.1

sentence-transformers 2.2.2 (huggingface-hub version compatible with 0.10.1)

scikit-learn 1.2.2

numpy 1.24.3

All dependencies pre-installed in Docker image for off-line usage.

Notes & Future Work
Presently uses extractive text truncation for refinement; potentially enhanced with lightweight summarization models.

Strong heading detection works well with varied document formats but can be made more effective using domain-adaptive heuristics.

Optimized for CPU-only setups; GPU acceleration achievable with model and pipeline extensions.

JSON schema and persona/job configurations are effortlessly customizable to meet different domains.

This README is for everyone involved: judges, developers, and collaborators, documenting the architecture and use to facilitate easy evaluation and deployment.