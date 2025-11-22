# ---- 1. Base image ----
FROM python:3.12-slim

# ---- 2. Set working directory ----
WORKDIR /app

# ---- 3. Install system dependencies ----
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---- 4. Copy project files ----
COPY . /app

# ---- 5. Install Python dependencies ----
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# ---- 6. Expose port ----
EXPOSE 8000

# ---- 7. Start the server ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
