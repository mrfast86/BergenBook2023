FROM python:3.11-slim

# Install Google Chrome stable (not Chromium — snap version breaks in containers)
RUN apt-get update && apt-get install -y wget gnupg ca-certificates --no-install-recommends \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub \
       | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] \
       http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /dev/shm && chmod 1777 /dev/shm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD streamlit run BergenBookSteamlit.py \
    --server.port ${PORT:-8080} \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.fileWatcherType none
