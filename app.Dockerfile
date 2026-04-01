# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the base working directory
WORKDIR /code

# Install system dependencies for PyAV (required by aiortc/streamlit-webrtc)
RUN apt-get update && apt-get install -y \
    libavdevice-dev \
    libavfilter-dev \
    libavformat-dev \
    libavcodec-dev \
    libswresample-dev \
    libswscale-dev \
    libavutil-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt /code/

# Install dependencies specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the frontend application code and utils
COPY ./app/ /code/app/
COPY ./utils/ /code/utils/

# Set the final working directory for running the app
WORKDIR /code/app

# Tell Python to also look for modules in the /code directory
ENV PYTHONPATH="/code"

# Make port 8501 available
EXPOSE 8501

# Run streamlit when the container launches
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
