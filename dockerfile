FROM python:3.10-slim

WORKDIR /app

COPY . /app/

# Install Chrome and its dependencies in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg2 \
    unzip \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && dpkg -i google-chrome-stable_current_amd64.deb || true \
    && apt-get -f install -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm google-chrome-stable_current_amd64.deb

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/google-chrome-stable
ENV CHROME_PATH=/usr/bin/google-chrome-stable

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8000

CMD ["sh", "-c", "python pipeline.py && python main.py"]