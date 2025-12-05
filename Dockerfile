FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Verify rulebook file exists and is valid YAML
RUN python -c "import yaml; yaml.safe_load(open('/app/complete_ca_rulebook_v2.yaml'))" || (echo 'ERROR: Rulebook YAML validation failed' && exit 1)

# Verify rulebook can be loaded by the loader
RUN python -c "import sys; sys.path.insert(0, '/app'); from ca_super_tool.engine.rulebook_loader import get_rulebook; rb = get_rulebook(); assert rb is not None and 'sections' in rb, 'Rulebook loading failed'" || (echo 'ERROR: Rulebook loader test failed' && exit 1)

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose port
EXPOSE 8000

# Use gunicorn with uvicorn worker class for production
# Render sets PORT environment variable dynamically
CMD ["sh", "-c", "gunicorn ca_super_tool.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}"]

