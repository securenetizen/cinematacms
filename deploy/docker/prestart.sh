#!/bin/bash

# Generate admin password
RANDOM_ADMIN_PASS=$(python -c "import secrets;chars = 'abcdefghijklmnopqrstuvwxyz0123456789';print(''.join(secrets.choice(chars) for i in range(10)))")
ADMIN_PASSWORD=${ADMIN_PASSWORD:-$RANDOM_ADMIN_PASS}

# Database setup and migrations
if [ "$ENABLE_MIGRATIONS" = "yes" ]; then
    echo "Running migrations and setup..."
    python manage.py migrate

    # Check if this is a fresh installation
    EXISTING_INSTALLATION=$(echo "from users.models import User; print(User.objects.exists())" | python manage.py shell)

    if [ "$EXISTING_INSTALLATION" != "True" ]; then
        echo "Setting up fresh installation..."
        python manage.py loaddata fixtures/encoding_profiles.json
        python manage.py loaddata fixtures/categories.json

        # Create superuser
        DJANGO_SUPERUSER_PASSWORD=$ADMIN_PASSWORD python manage.py createsuperuser \
            --no-input \
            --username=$ADMIN_USER \
            --email=$ADMIN_EMAIL \
            --database=default || true
        echo "Created admin user with password: $ADMIN_PASSWORD"
    else
        echo "Using existing installation"
    fi

    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

# Setup nginx configuration
echo "Configuring nginx..."
cp deploy/docker/nginx_http_only.conf /etc/nginx/sites-available/default
cp deploy/docker/nginx_http_only.conf /etc/nginx/sites-enabled/default
cp deploy/docker/uwsgi_params /etc/nginx/sites-enabled/uwsgi_params
cp deploy/docker/nginx.conf /etc/nginx/

# Setup supervisord base configuration
cp deploy/docker/supervisord/supervisord-debian.conf /etc/supervisor/conf.d/supervisord-debian.conf

# Setup optional services
services="UWSGI:uwsgi NGINX:nginx CELERY_BEAT:celery_beat CELERY_SHORT:celery_short CELERY_LONG:celery_long"

for service in $services; do
    env_var=$(echo "$service" | cut -d':' -f1)
    config_name=$(echo "$service" | cut -d':' -f2)
    env_value=$(printenv "ENABLE_$env_var")
    if [ "$env_value" = "yes" ]; then
        echo "Enabling $config_name service..."
        cp "deploy/docker/supervisord/supervisord-$config_name.conf" "/etc/supervisor/conf.d/supervisord-$config_name.conf"

        # Special cleanup for celery-long
        if [ "$config_name" = "celery_long" ]; then
            rm -f /var/run/cinematacms/* # Remove stale process files
        fi
    fi
done

# Create user logos directory and default avatar
echo "Creating default user avatar..."
mkdir -p /home/cinemata/cinematacms/media_files/userlogos
wget -O /home/cinemata/cinematacms/media_files/userlogos/user.jpg https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y