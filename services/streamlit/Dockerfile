# Use official Python 3.11 slim base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the Streamlit service requirements file
COPY services/streamlit/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit default port
EXPOSE 8501
EXPOSE 8002
