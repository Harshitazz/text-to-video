FROM python:3.11-slim

WORKDIR /app
RUN apt update && apt install -y iputils-ping curl

# Install system dependencies and ImageMagick
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libmagickwand-dev \
    && rm -rf /var/lib/apt/lists/*

# Download and install specific ImageMagick version
RUN cd /tmp && \
    wget https://download.imagemagick.org/ImageMagick/download/releases/ImageMagick-6.9.13-21.tar.gz && \
    tar xvzf ImageMagick-6.9.13-21.tar.gz && \
    cd ImageMagick-6.9.13-21 && \
    ./configure && \
    make && \
    make install && \
    ldconfig /usr/local/lib && \
    rm -rf /tmp/ImageMagick*

RUN convert --version
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 80
RUN mkdir -p static


# CMD uvicorn app:app --host 0.0.0.0 --port $80
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]