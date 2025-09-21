FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY . .

# Install dependencies
RUN uv sync --frozen || (uv venv && uv pip install -r requirements.txt)

# Set environment variables
ENV PORT=8080

# Use the exact command that works locally
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0", "--server.headless", "true", "--server.enableCORS", "false"]
