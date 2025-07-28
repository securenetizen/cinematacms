server {
    listen 80;
    server_name localhost

    gzip on;
    access_log /var/log/nginx/mediacms.io.access.log;

    error_log  /var/log/nginx/mediacms.io.error.log  warn;

#    # redirect to https if logged in
#    if ($http_cookie ~* "sessionid") {
#        rewrite  ^/(.*)$  https://localhost/$1  permanent;
#    }

#    # redirect basic forms to https
#    location ~ (login|login_form|register|mail_password_form)$ {
#        rewrite  ^/(.*)$  https://localhost/$1  permanent;
#    }

    location /static {
        alias /home/cinemata/cinematacms/static ;
    }

    location /media/original {
        alias /home/cinemata/cinematacms/media_files/original;
    }

    location /media {
        alias /home/cinemata/cinematacms/media_files ;
    }

    location / {

        include /etc/nginx/uwsgi_params;
        uwsgi_pass 127.0.0.1:9000;
    }
}

# Upload subdomain for file uploads
server {
    listen 80;
    server_name uploads.localhost;
 gzip on;
    access_log /var/log/nginx/upload.localhost.access.log;
    error_log  /var/log/nginx/upload.localhost.error.log warn;

    # Redirect all non-upload requests to main domain
    location / {
        return 301 http://localhost$request_uri;
    }

    # Handle file upload endpoint with dynamic CORS
    location /fu/ {

        include /etc/nginx/uwsgi_params;
        uwsgi_pass 127.0.0.1:9000;
    }
}

server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate_key  /etc/letsencrypt/live/localhost/privkey.pem;
    ssl_certificate  /etc/letsencrypt/live/localhost/fullchain.pem;
    ssl_dhparam /etc/nginx/dhparams/dhparams.pem;

    ssl_protocols TLSv1.2 TLSv1.3; # Dropping SSLv3, ref: POODLE
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_ecdh_curve secp521r1:secp384r1;
    ssl_prefer_server_ciphers on;

    gzip on;
    access_log /var/log/nginx/mediacms.io.access.log;

    error_log  /var/log/nginx/mediacms.io.error.log  warn;

    location /static {
        alias /home/cinemata/cinematacms/static ;
    }

    location /media/original {
        alias /home/cinemata/cinematacms/media_files/original;
        #auth_basic "auth protected area";
        #auth_basic_user_file /home/cinemata/cinematacms/deploy/local_install/.htpasswd;
    }

    location /media {
        alias /home/cinemata/cinematacms/media_files ;
    }

    location / {

        include /etc/nginx/uwsgi_params;
        uwsgi_pass 127.0.0.1:9000;
    }
}

# Upload subdomain for file uploads (HTTPS)
server {
    listen 443 ssl;
    server_name uploads.localhost;

    ssl_certificate_key  /etc/letsencrypt/live/localhost/privkey.pem;
    ssl_certificate  /etc/letsencrypt/live/localhost/fullchain.pem;
    ssl_dhparam /etc/nginx/dhparams/dhparams.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_ecdh_curve secp521r1:secp384r1;
    ssl_prefer_server_ciphers on;

     # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;

    gzip on;
    access_log /var/log/nginx/uploads.localhost.access.log;
    error_log  /var/log/nginx/uploads.localhost.error.log warn;

    # Redirect all non-upload requests to main domain
    location / {
        return 301 https://localhost$request_uri;
    }

    # Handle file upload endpoint
    location /fu/ {

        proxy_request_buffering off;
        include /etc/nginx/uwsgi_params;
        uwsgi_pass 127.0.0.1:9000;
    }

    # Health check endpoint for monitoring
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
        add_header 'Access-Control-Allow-Origin' '*' always;
    }

    # Block all other paths on upload subdomain
    location ~ ^/(?!fu/|health) {
        return 301 https://localhost$request_uri;
    }
}
