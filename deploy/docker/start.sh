#!/usr/bin/env sh
set -e

# Run prestart script if it exists
if [ -f deploy/docker/prestart.sh ]; then
    echo "Running prestart script..."
    . deploy/docker/prestart.sh
fi

# Start server
echo "Starting server..."
exec /usr/bin/supervisord
