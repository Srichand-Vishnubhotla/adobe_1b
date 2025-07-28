FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY process_documents.py ./
COPY schema ./schema/
COPY persona_job.txt ./

VOLUME ["/app/input", "/app/output"]

CMD ["python", "process_documents.py", \
     "--input_dir", "/app/input", \
     "--output_dir", "/app/output", \
     "--persona_file", "/app/persona_job.txt", \
     "--schema_path", "/app/schema/challenge1b_output_schema.json"]
