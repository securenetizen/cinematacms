# Upload Subdomain Configuration for CinemataCMS

This document explains how the upload subdomain (`upload.cinemata.org`) is configured to handle file uploads through the `/fu/` endpoint.

## Overview

The upload subdomain has been configured to:
- Handle all file upload operations through the `/fu/` endpoint
- Redirect all other requests to the main domain
- Support both HTTP and HTTPS
- Allow large file uploads up to 800MB

## Configuration Components

The upload subdomain is now fully configurable through Django settings, eliminating hardcoded values.

### 1. Nginx Configuration

The nginx configuration (`deploy/mediacms.io`) includes two server blocks for the upload subdomain:

#### HTTP (Port 80)
```nginx
server {
    listen 80;
    server_name upload.cinemata.org;

    # Redirect all non-upload requests to main domain
    location / {
        return 301 http://cinemata.org$request_uri;
    }

    # Handle file upload endpoint
    location /fu/ {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,X-CSRFToken';
        add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range';

        client_max_body_size 800M;

        include /etc/nginx/sites-enabled/uwsgi_params;
        uwsgi_pass 127.0.0.1:9000;
    }
}
```

#### HTTPS (Port 443)
Similar configuration with SSL settings enabled.

### 2. Django Settings

The Django settings have been updated to include a configurable upload subdomain:

#### Upload Subdomain Configuration
```python
# Upload subdomain configuration
UPLOAD_SUBDOMAIN = "upload.cinemata.org"
```

#### Dynamic Host Configuration
The system automatically adds the upload subdomain to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`:

```python
# Dynamic host configuration
main_domain = FRONTEND_HOST.replace("http://", "").replace("https://", "")
ALLOWED_HOSTS.extend([main_domain, UPLOAD_SUBDOMAIN])

# Dynamic CSRF trusted origins
CSRF_TRUSTED_ORIGINS.extend([
    f"http://{main_domain}",
    f"https://{main_domain}",
    f"http://{UPLOAD_SUBDOMAIN}",
    f"https://{UPLOAD_SUBDOMAIN}",
])
```

### 3. Frontend Configuration

The frontend FineUploader configuration uses dynamic template variables instead of hardcoded URLs:

```javascript
request: {
    endpoint: '<%= UPLOAD_HOST %>/fu/upload/',
    customHeaders: {
        'X-CSRFToken': getCSRFToken('csrftoken')
    }
},
// ...
chunking: {
    // ...
    success: {
        endpoint: '<%= UPLOAD_HOST %>/fu/upload/?done'
    }
}
```

The `UPLOAD_HOST` variable is automatically generated based on the request protocol (HTTP/HTTPS) and the `UPLOAD_SUBDOMAIN` setting.

## Environment Variable Configuration

You can configure the upload subdomain using the `UPLOAD_SUBDOMAIN` environment variable:

```bash
# In your environment or .env file
UPLOAD_SUBDOMAIN=upload.yourdomain.com
```

This simplifies configuration across different environments without hardcoding values in settings files.

## Customization

### Changing the Upload Subdomain

To use a different upload subdomain, you can either set an environment variable or update the Django configuration:

```bash
# Option 1: Environment variable (recommended)
export UPLOAD_SUBDOMAIN="files.yourdomain.com"
```

```python
# Option 2: In cms/settings.py or cms/local_settings.py
UPLOAD_SUBDOMAIN = "files.yourdomain.com"  # Custom subdomain
```

The system will automatically:
- Add the new subdomain to `ALLOWED_HOSTS`
- Configure CSRF trusted origins
- Generate the correct frontend URLs

### Environment-Specific Configuration

You can configure different subdomains for different environments using environment variables:

```bash
# Development
UPLOAD_SUBDOMAIN="upload-dev.cinemata.org"

# Staging
UPLOAD_SUBDOMAIN="upload-staging.cinemata.org"

# Production
UPLOAD_SUBDOMAIN="upload.cinemata.org"
```

## Setup Instructions

### 1. DNS Configuration

Add the following DNS records to your domain configuration:

```
upload.cinemata.org    A    <your-server-ip>
```

Or for local development, add to your `/etc/hosts` file:
```
127.0.0.1    upload.cinemata.org
```

### 2. SSL Certificate (for HTTPS)

If using SSL, ensure your certificate covers the upload subdomain. For Let's Encrypt:

```bash
certbot certonly --nginx -d cinemata.org -d upload.cinemata.org
```

### 3. Nginx Reload

After configuration changes, reload nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Benefits

1. **Separation of Concerns**: Upload operations are isolated from the main site
2. **Performance**: Upload-specific optimizations without affecting the main site
3. **Security**: Better control over upload-specific security settings
4. **Scalability**: Can be scaled independently or moved to a different server
5. **Monitoring**: Separate logging for upload operations

## URL Structure

- Main site: `http://cinemata.org/` or `https://cinemata.org/`
- Upload endpoint: `http://upload.cinemata.org/fu/upload/` or `https://upload.cinemata.org/fu/upload/`
- All other URLs on upload subdomain redirect to main domain

## Troubleshooting

### CSRF Token Issues
If you encounter CSRF token errors, ensure:
1. `CSRF_TRUSTED_ORIGINS` includes both domains
2. The frontend is correctly passing the CSRF token in headers
3. Both domains are serving from the same Django instance

### Upload Size Limits
The nginx configuration sets `client_max_body_size 800M`. Adjust this value based on your needs:

```nginx
client_max_body_size 2G;  # For 2GB uploads
```

### CORS Issues
The nginx configuration includes CORS headers. If you need more restrictive CORS policies, modify the `Access-Control-Allow-Origin` header to specify allowed domains instead of using `*`.

## Development vs Production

### Development
- Uses `upload.cinemata.org` for local testing
- May use HTTP for simplicity
- DNS typically handled via `/etc/hosts`

### Production
- Should use proper DNS records
- Must use HTTPS for security
- Consider using a CDN or dedicated upload server for better performance