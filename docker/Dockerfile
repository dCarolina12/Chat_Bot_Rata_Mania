FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files y dependencias de datos
COPY main.py .
COPY gradio_e.py .
COPY negocio.json .
COPY reservas.json .
COPY ratas.db .
COPY scripts/ ./scripts/

# Otorgar permisos de ejecución al script bash llamado por main.py
RUN chmod +x scripts/ratadb.sh

# Create data directory for persistence
RUN mkdir -p /data

# Expose ports
# - 8011: FastAPI main application
# - 7860: Gradio interface
EXPOSE 8011 7860

# Environment variables that MUST be set at runtime:
# - GROQ_API_KEY: Your Groq API key
# - GROQ_MODEL: Groq model name (e.g., llama-3.3-70b-versatile)
# - CHATBOT_API_URL: URL of the FastAPI service (set by docker compose)

# Start both services (Comando por defecto si se corre el contenedor individualmente)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8011 & python gradio_e.py"]
