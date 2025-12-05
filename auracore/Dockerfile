FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api/ ./api/
COPY prompts/ ./prompts/

# Create directories
RUN mkdir -p /opt/auracore/prompts /opt/auracore/logs

# Copy prompts to expected location
COPY prompts/ /opt/auracore/prompts/

# Environment variables
ENV OLLAMA_URL=http://ollama:11434/api/generate
ENV DIAGNOSTIC_MODEL=qwen2.5-coder:3b-instruct
ENV VALIDATION_MODEL=phi3:mini
ENV LLM_TIMEOUT=180.0
ENV PROMPTS_DIR=/opt/auracore/prompts

EXPOSE 8900

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8900"]
