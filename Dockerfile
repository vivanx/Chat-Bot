FROM python:3.9-slim

# Install Rust and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set a writable Cargo home directory
ENV CARGO_HOME=/app/.cargo
RUN mkdir -p /app/.cargo

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variable for Render
ENV PORT=8000

# Run the bot
CMD ["python", "main.py"]
