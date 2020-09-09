FROM python:3.8-alpine

# Install requirements
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy assets
COPY assets/ /opt/resource/
