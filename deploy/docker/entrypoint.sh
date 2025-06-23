#!/bin/bash
set -e

# Forward logs to docker log collector
ln -sf /dev/stdout /var/log/nginx/access.log
ln -sf /dev/stderr /var/log/nginx/error.log
ln -sf /dev/stdout /var/log/nginx/cinemata.access.log
ln -sf /dev/stderr /var/log/nginx/cinemata.error.log

# Copy local settings
cp /home/cinemata/cinematacms/deploy/docker/local_settings.py /home/cinemata/cinematacms/cms/local_settings.py

# Create necessary directories and files
mkdir -p /home/cinemata/cinematacms/{logs,media_files/hls}
touch /home/cinemata/cinematacms/logs/debug.log
mkdir -p /var/run/cinematacms

# Set up permissions
TARGET_GID=$(stat -c "%g" /home/cinemata/cinematacms/)
find /home/cinemata/cinematacms ! -path "*/.git/*" -exec chown -h www-data:$TARGET_GID {} + 2>/dev/null || true
chown www-data:www-data /var/run/cinematacms

# Make scripts executable
chmod +x /home/cinemata/cinematacms/deploy/docker/{start.sh,prestart.sh}

exec "$@"
