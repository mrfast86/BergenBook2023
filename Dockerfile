FROM python:3.12-slim

# Install Chromium
RUN apt-get update && apt-get install -y chromium chromium-driver wget unzip

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV STREAMLIT_WATCHDOG="false"

# Copy application code
COPY . .

# Streamlit config
ENV STREAMLIT_SERVER_PORT=$PORT
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Chrome binary path
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH=$PATH:/usr/bin/chromium

# Expose port
EXPOSE $PORT

# Start Streamlit — shell form to resolve $PORT ✅
CMD streamlit run BergenBook.py --server.port $PORT --server.address 0.0.0.0
