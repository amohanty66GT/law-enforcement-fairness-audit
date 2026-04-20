# Start from an official Python image. We pin the version so the build is
# reproducible — "slim" means it's a smaller base without unnecessary tools.
FROM python:3.11-slim

# Set the working directory inside the container. All subsequent commands
# run relative to this path.
WORKDIR /app

# Install system-level dependencies that some Python packages need to compile.
# We clean up the apt cache in the same layer to keep the image size down.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — before the rest of the code. Docker caches each
# layer, so if your code changes but requirements don't, it skips reinstalling
# packages on the next build. This makes rebuilds much faster.
COPY requirements.txt .

# Install Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application code into the container.
COPY . .

# Create directories the app expects to exist at runtime.
RUN mkdir -p logs output data

# Tell Docker which port the Streamlit dashboard listens on.
# This is documentation — you still need to publish the port when running.
EXPOSE 8501

# Set environment variables for Streamlit so it runs cleanly in a container
# (no browser auto-open, no usage stats, bind to all interfaces).
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# The default command when the container starts — launches the dashboard.
# You can override this at runtime to run the analysis script instead.
CMD ["streamlit", "run", "src/dashboard/app.py"]
