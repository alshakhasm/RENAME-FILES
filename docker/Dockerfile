# Date Prefix File Renamer - Dockerfile
# Multi-stage build for production-ready container

FROM python:3.11-slim as builder

# Install system dependencies for GUI support
RUN apt-get update && apt-get install -y \
    python3-tk \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies for GUI
RUN apt-get update && apt-get install -y \
    python3-tk \
    x11-apps \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash renamer

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/renamer/.local

# Copy application source
COPY src/ ./src/
COPY modern_gui.py .
COPY web_app.py .
COPY templates/ ./templates/
COPY setup.py .
COPY README.md* .

# Copy Docker-specific files
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set ownership and permissions
RUN chown -R renamer:renamer /app
RUN chown renamer:renamer /entrypoint.sh

# Switch to non-root user
USER renamer

# Add user Python packages to PATH
ENV PATH=/home/renamer/.local/bin:$PATH
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Set display for X11 forwarding (can be overridden)
ENV DISPLAY=:0

# Create mount point for data
VOLUME ["/data"]

# Expose web interface port
EXPOSE 8080

# Set default working directory for file operations
WORKDIR /data

# Use entrypoint script for mode detection
ENTRYPOINT ["/entrypoint.sh"]

# Default to web mode
CMD ["web"]