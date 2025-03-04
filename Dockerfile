FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for QR codes and logs
RUN mkdir -p /app/qr_codes
RUN mkdir -p /app/logs

# Expose web server port
EXPOSE 8080

# Set environment variables with defaults
ENV SCHOOL_URL="https://qehsn.ha.org.hk" \
    USERNAME="" \
    PASSWORD="" \
    INTERVAL_MINUTES=30 \
    OUTPUT_DIR="/app/qr_codes"

# Run the application
CMD ["python", "app.py"]
