FROM python:3.10-bookworm

SHELL ["/bin/bash", "-c"]

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CELERY_APP='cms' \
    VIRTUAL_ENV=/home/cinemata \
    PATH="$VIRTUAL_ENV/bin:$PATH" \
    ENABLE_UWSGI='yes' \
    ENABLE_NGINX='yes' \
    ENABLE_CELERY_BEAT='yes' \
    ENABLE_CELERY_SHORT='yes' \
    ENABLE_CELERY_LONG='yes' \
    ENABLE_MIGRATIONS='yes'

# Install system dependencies, ffmpeg, and Bento4 in one layer
RUN apt-get update -y && \
    apt-get -y upgrade && \
    apt-get install --no-install-recommends -y \
        supervisor nginx imagemagick procps pkg-config \
        libxml2-dev libxmlsec1-dev libxmlsec1-openssl \
        python3-venv wget xz-utils unzip && \
    # Install ffmpeg
    wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && \
    mkdir -p ffmpeg-tmp && \
    tar -xf ffmpeg-release-amd64-static.tar.xz --strip-components 1 -C ffmpeg-tmp && \
    cp -v ffmpeg-tmp/ffmpeg ffmpeg-tmp/ffprobe ffmpeg-tmp/qt-faststart /usr/local/bin && \
    rm -rf ffmpeg-tmp ffmpeg-release-amd64-static.tar.xz && \
    # Install Bento4
    mkdir -p /home/cinemata/bento4 && \
    wget -q http://zebulon.bok.net/Bento4/binaries/Bento4-SDK-1-6-0-637.x86_64-unknown-linux.zip && \
    unzip Bento4-SDK-1-6-0-637.x86_64-unknown-linux.zip -d /home/cinemata/bento4 && \
    mv /home/cinemata/bento4/Bento4-SDK-1-6-0-637.x86_64-unknown-linux/* /home/cinemata/bento4/ && \
    rm -rf /home/cinemata/bento4/Bento4-SDK-1-6-0-637.x86_64-unknown-linux \
           /home/cinemata/bento4/docs \
           Bento4-SDK-1-6-0-637.x86_64-unknown-linux.zip && \
    # Cleanup
    rm -rf /var/lib/apt/lists/* && \
    apt-get purge --auto-remove -y wget xz-utils unzip && \
    apt-get clean

# Set up application directory and virtual environment
RUN mkdir -p /home/cinemata/cinematacms/logs && \
    cd /home/cinemata && \
    python3 -m venv $VIRTUAL_ENV

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --no-binary lxml,xmlsec -r requirements.txt

# Copy application files and set working directory
COPY . /home/cinemata/cinematacms
WORKDIR /home/cinemata/cinematacms

# Make entrypoint executable
RUN chmod +x ./deploy/docker/entrypoint.sh

EXPOSE 9000 80

ENTRYPOINT ["./deploy/docker/entrypoint.sh"]
CMD ["./deploy/docker/start.sh"]
