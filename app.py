import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import dari backend yang sudah ada
from backend_fastapi import app

# Hugging Face Spaces akan menggunakan app ini
# File backend_fastapi.py sudah lengkap, jadi kita tinggal re-export

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))  # Hugging Face default port
    uvicorn.run(app, host="0.0.0.0", port=port)