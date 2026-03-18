# Use official Python slim image (Pinned to 3.11.11-slim-bookworm for reproducibility)
FROM python:3.11.11-slim-bookworm@sha256:080000300df6664294f61821f93ca60f6eeec92c3a039da983799caacda544f1 as builder

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11.11-slim-bookworm@sha256:080000300df6664294f61821f93ca60f6eeec92c3a039da983799caacda544f1

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-root user
RUN groupadd -g 10001 botgroup && \
    useradd -u 10001 -g botgroup -m -s /bin/bash botuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code with proper ownership
COPY --chown=botuser:botgroup . .

# Switch to non-root user
USER botuser

# Command to run the bot
CMD ["python", "main.py"]
