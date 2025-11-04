FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (jika diperlukan)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (untuk caching layer)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy file-file yang diperlukan untuk backend
COPY backend_fastapi.py .
COPY inference_rf.py .
COPY rf_total_coliform_log1p_improved.joblib .
COPY model_features_order.txt .

# Expose port untuk Hugging Face Spaces
EXPOSE 7860

# Set environment variables
ENV PORT=7860 \
    MODEL_PATH=rf_total_coliform_log1p_improved.joblib \
    FEATURES_ORDER_PATH=model_features_order.txt \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:7860/docs')" || exit 1

# Run aplikasi
CMD ["uvicorn", "backend_fastapi:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]