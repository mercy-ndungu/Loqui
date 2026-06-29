FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm

COPY . .

RUN python - <<'PY'
import nltk
for pkg in ("punkt", "punkt_tab"):
    nltk.download(pkg, quiet=True)
PY

ENV ENVIRONMENT=production
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
