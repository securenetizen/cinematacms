# Upload Subdomain Configuration for CinemataCMS

This document explains how the upload subdomain (`upload.cinemata.org`) is configured to handle file uploads through the `/fu/` endpoint.

## Overview

The upload subdomain has been configured to:
- Handle all file upload operations through the `/fu/` endpoint
- Redirect all other requests to the main domain
- Support both HTTP and HTTPS with forced HTTPS in production
- Allow large file uploads
- Implement CORS and CSRF protection for secure cross-domain uploads

## Configuration Components

The upload subdomain is fully configurable through Django settings, eliminating hardcoded values.

### 1. Nginx Configuration

The nginx configuration includes server blocks for the upload subdomain with security measures:

> **Note**: CORS handling has been moved from nginx to Django middleware for better control and flexibility. The nginx configuration focuses on SSL termination, request routing, and basic security headers.

#### HTTP (Port 80) - Force HTTPS
```nginx
server {
    listen 80;
    server_name upload.cinemata.org;

    # Force HTTPS for all requests
    return 301 https://$server_name$request_uri;
}
```

#### HTTPS (Port 443) - Main Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name upload.cinemata.org;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/upload.cinemata.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/upload.cinemata.org/privkey.pem;
    ssl_dhparam /etc/nginx/dhparams/dhparams.pem;

    # Modern SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;

    # Upload-specific optimizations
    client_max_body_size 800M;
    proxy_request_buffering off;
    proxy_buffering off;

    # Redirect all non-upload requests to main domain
    location / {
        return 301 https://cinemata.org$request_uri;
    }

    # File upload endpoint - CORS handled by Django middleware
    location /fu/ {
        # Pass to Django application
        include /etc/nginx/uwsgi_params;
        uwsgi_pass 127.0.0.1:9000;
    }

    # Health check endpoint for monitoring
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Block all other paths on upload subdomain
    location ~ ^/(?!fu/|health) {
        return 301 https://cinemata.org$request_uri;
    }
}
```

### 2. Django Settings

The Django settings include security configurations for cross-domain uploads:

#### Upload Subdomain Configuration
```python
# Upload subdomain configuration
UPLOAD_SUBDOMAIN = os.getenv('UPLOAD_SUBDOMAIN', 'upload.cinemata.org')

# Allowed hosts configuration
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "cinemata.org",
    "www.cinemata.org",
    "upload.cinemata.org",
    ".cinemata.org",
]

# CSRF Trusted Origins for cross-domain uploads
CSRF_TRUSTED_ORIGINS = [
    "https://cinemata.org",
    "https://www.cinemata.org",
    "https://upload.cinemata.org",
]

# Cookie Settings for Cross-Domain Support
SESSION_COOKIE_DOMAIN = ".cinemata.org"
CSRF_COOKIE_DOMAIN = ".cinemata.org"
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
```

#### Security Middleware Configuration

```python
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # Django CORS Headers middleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "users.middleware.AdminMFAMiddleware",
]
```

### 3. CORS Configuration

The system uses Django CORS Headers middleware for cross-domain request handling instead of nginx CORS configuration. This approach provides better control and flexibility for handling complex CORS scenarios.

> **Important**: CORS handling has been moved from nginx to Django middleware. The main site nginx configuration no longer includes CORS headers, as they are now handled by Django's `corsheaders.middleware.CorsMiddleware`.

#### Django CORS Headers Configuration

```python
# CORS configuration in settings.py
CORS_ALLOWED_ORIGINS = [
    "https://cinemata.org",
    "https://www.cinemata.org",
    "https://upload.cinemata.org",
]
CORS_ALLOW_CREDENTIALS = True

# Import default headers to extend them
from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = default_headers + (
    'x-requested-with',     # Add X-Requested-With
    'if-modified-since',    # Add If-Modified-Since
    'cache-control',        # Add Cache-Control
    'content-type',         # Add Content-Type (important for application/json etc.)
    'range',                # Add Range
    'dnt',                  # Generally not needed as DNT is safelisted
    'user-agent',           # Generally not needed as User-Agent is safelisted
)

# Crucial for exposing response headers to frontend JavaScript
CORS_EXPOSE_HEADERS = [
    'Content-Length',
    'Content-Range',
]

# Development fallback (in local_settings.py)
# CORS_ORIGIN_ALLOW_ALL = True
```

#### CORS Architecture Decision

The system previously used nginx CORS headers but has been migrated to Django CORS Headers middleware for the following reasons:

1. **Better Control**: Django middleware provides more granular control over CORS policies
2. **Dynamic Configuration**: CORS settings can be configured per environment without nginx changes
3. **Integration**: Better integration with Django's authentication and session management
4. **Debugging**: Easier to debug CORS issues within the Django application
5. **Maintenance**: Centralized CORS configuration in Django settings instead of split between nginx and Django

The main site nginx configuration has been simplified and CORS headers removed, delegating all CORS handling to Django middleware.

### 4. Frontend Configuration

The frontend FineUploader configuration includes security features:

```javascript
var uploader = new qq.FineUploader({
    debug: false,
    element: document.querySelector('.media-uploader'),
    request: {
        endpoint: '{{UPLOAD_HOST}}{% url "uploader:upload" %}',
        customHeaders: {
            'X-CSRFToken': getCSRFToken('csrftoken')  // CSRF token from cookie
        },
        withCredentials: true  // Send cookies with cross-origin requests
    },
    validation: {
        itemLimit: {{UPLOAD_MAX_FILES_NUMBER}},
        sizeLimit: {{UPLOAD_MAX_SIZE}},
    },
    cors: {
        expected: true,  // Enable CORS support
        sendCredentials: true  // Send credentials for CORS requests
    },
    chunking: {
        enabled: true,  // Enable chunked uploads for large files
        concurrent: {
            enabled: true  // Enable concurrent chunk uploads
        },
        success: {
            endpoint: '{{UPLOAD_HOST}}{% url "uploader:upload" %}?done',
        },
    },
    retry: {
        enableAuto: true,
        maxAutoAttempts: 2,
    },
});
```

## Security Features

### 🔐 Authentication & Authorization

1. **User Permission Validation**
   ```python
   def user_allowed_to_upload(request):
       if request.user.is_anonymous:
           return False
       if request.user.is_superuser:
           return True

       # Check user permissions based on settings
       if settings.CAN_ADD_MEDIA == "all":
           return True
       elif settings.CAN_ADD_MEDIA == "email_verified":
           return request.user.email_is_verified
       elif settings.CAN_ADD_MEDIA == "advancedUser":
           return request.user.advancedUser

       return False
   ```

2. **CSRF Protection**
   - All upload requests require valid CSRF tokens
   - Tokens are validated from both headers and cookies
   - Cross-origin requests are properly handled

3. **Session Security**
   - Secure cookie settings for cross-domain authentication
   - Session timeout configuration
   - SameSite cookie policies

### 🌐 Network Security

1. **CORS Configuration**
   - Django CORS Headers middleware handles all CORS requests (nginx CORS headers removed)
   - Whitelist-based origin control using `CORS_ALLOWED_ORIGINS`
   - Credentials support for authenticated uploads (`CORS_ALLOW_CREDENTIALS = True`)
   - Development fallback with `CORS_ORIGIN_ALLOW_ALL = True`
   - Proper preflight request handling by Django middleware
   - Simplified nginx configuration without CORS headers

## Setup Instructions

### 1. DNS Configuration

Add the following DNS records to your domain configuration:

```dns
upload.cinemata.org    A    <your-server-ip>
```

Or for local development, add to your `/etc/hosts` file:

```hosts
127.0.0.1    upload.cinemata.org
```

### 2. Remove CORS Headers from Main Site Nginx Configuration

Before setting up the upload subdomain, you need to remove CORS headers from the main site nginx configuration since CORS is now handled by Django middleware:

```bash
# 1. Backup your current nginx configuration
sudo cp /etc/nginx/sites-available/mediacms.io /etc/nginx/sites-available/mediacms.io.backup

# 2. Edit the main site nginx configuration
sudo nano /etc/nginx/sites-available/mediacms.io
```

**Remove the following CORS-related headers from your main site nginx configuration:**

```nginx
# Remove these lines if they exist in your nginx configuration:
add_header Access-Control-Allow-Origin *;
add_header Access-Control-Allow-Methods "GET, POST, OPTIONS, PUT, DELETE";
add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
add_header Access-Control-Expose-Headers "Content-Length,Content-Range";
add_header Access-Control-Allow-Credentials true;

# Also remove any location blocks specifically for OPTIONS requests like:
# location ~* \.(eot|ttf|woff|woff2)$ {
#     add_header Access-Control-Allow-Origin *;
# }

# Or any other CORS-related add_header directives
```

**Test and reload nginx after removing CORS headers:**

```bash
# 3. Test nginx configuration
sudo nginx -t

# 4. If test passes, reload nginx
sudo systemctl reload nginx

```

### 3. Upload Subdomain Nginx Configuration

Use the dedicated upload subdomain configuration:

```bash
# Copy the upload subdomain configuration
sudo cp deploy/upload-subdomain.conf /etc/nginx/sites-available/upload.cinemata.org

# Make sure to change the domain name
sudo nano /etc/nginx/sites-available/upload.cinemata.org

# Test configuration
sudo nginx -t

```

### 4. SSL Certificate (Required for Production)

Ensure your certificate covers the upload subdomain. For Let's Encrypt:

```bash
# Get certificate for both main domain and upload subdomain
certbot certonly --nginx -d cinemata.org -d upload.cinemata.org

# Or use separate certificates
certbot certonly --nginx -d upload.cinemata.org
```

### 5. Enable Nginx Configuration

```bash
# Edit the Nginx configuration to include the newly generated ssl certificate paths
sudo nano /etc/nginx/sites-available/upload.cinemata.org
sudo nano /etc/nginx/sites-enabled/mediacms.io

# Enable the upload subdomain configuration
sudo ln -s /etc/nginx/sites-available/upload.cinemata.org /etc/nginx/sites-enabled/ upload.cinemata.org
# Reload Nginx to apply changes
sudo systemctl reload nginx
```

### 6. Django Settings (OPTIONAL)

Update your Django settings to include the upload subdomain configuration:

```python
# In cms/local_settings.py or cms/settings.py
UPLOAD_SUBDOMAIN = os.getenv('UPLOAD_SUBDOMAIN', 'upload.cinemata.org')

# Update ALLOWED_HOSTS to include the upload subdomain
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "cinemata.org",
    "www.cinemata.org",
    "upload.cinemata.org",
    ".cinemata.org",
]

# Add to CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = [
    "https://cinemata.org",
    "https://www.cinemata.org",
    "https://upload.cinemata.org",
]

# Update CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS = [
    "https://cinemata.org",
    "https://www.cinemata.org",
    "https://upload.cinemata.org",
]
```

## Customization

### Changing the Upload Subdomain

To use a different upload subdomain, update the following settings:

```python
# Update the upload subdomain
UPLOAD_SUBDOMAIN = "files.yourdomain.com"

# Update ALLOWED_HOSTS to include your new subdomain
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "yourdomain.com",
    "www.yourdomain.com",
    "files.yourdomain.com",
    ".yourdomain.com",
]

# Update CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://files.yourdomain.com",
]

# Update CORS_ALLOWED_ORIGINS
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://files.yourdomain.com",
]
```


## Monitoring & Logging

### Upload-Specific Logging

```nginx
# Separate log files for upload subdomain
access_log /var/log/nginx/upload.cinemata.org.access.log;
error_log  /var/log/nginx/upload.cinemata.org.error.log warn;
```

### Health Monitoring

The upload subdomain includes a health check endpoint:

```nginx
location /health {
    access_log off;
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}
```

## Troubleshooting

### CORS Migration Issues

If you're migrating from nginx CORS to Django CORS middleware and experiencing issues:

1. **Verify all nginx CORS headers have been removed**:
   ```bash
   # Check your main site nginx configuration for any remaining CORS headers
   sudo grep -i "access-control" /etc/nginx/sites-available/mediacms.io

   # This command should return no results if all CORS headers are removed
   ```

2. **Check for conflicting CORS headers**:
   ```bash
   # Test if nginx is still sending CORS headers (should not show any Access-Control headers)
   curl -I https://cinemata.org

   # Test if Django middleware is working (should show CORS headers)
   curl -H "Origin: https://cinemata.org" -I https://cinemata.org/
   ```

3. **Verify Django CORS middleware is properly configured**:
   ```python
   # In settings.py, ensure CorsMiddleware is first in MIDDLEWARE
   MIDDLEWARE = [
       "corsheaders.middleware.CorsMiddleware",  # Must be first
       "django.middleware.security.SecurityMiddleware",
       # ... other middleware
   ]
   ```

4. **Common nginx CORS remnants to remove**:
   ```nginx
   # Remove ALL of these from your nginx configuration:
   add_header Access-Control-Allow-Origin $http_origin always;
   add_header Access-Control-Allow-Credentials true always;
   add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
   add_header Access-Control-Allow-Headers "Accept,Authorization,Cache-Control,Content-Type,DNT,If-Modified-Since,Keep-Alive,Origin,User-Agent,X-Requested-With" always;
   add_header Access-Control-Expose-Headers "Content-Length,Content-Range" always;

   # Also remove any location blocks handling OPTIONS requests for CORS
   if ($request_method = 'OPTIONS') {
       add_header Access-Control-Allow-Origin $http_origin;
       add_header Access-Control-Allow-Methods 'GET, POST, OPTIONS';
       add_header Access-Control-Allow-Headers 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range';
       add_header Access-Control-Max-Age 1728000;
       add_header Content-Type 'text/plain; charset=utf-8';
       add_header Content-Length 0;
       return 204;
   }
   ```

### CSRF Token Issues

If you encounter CSRF token errors:

1. **Check CSRF Trusted Origins**
   ```python
   # Ensure both domains are included
   CSRF_TRUSTED_ORIGINS = [
       "https://cinemata.org",
       "https://upload.cinemata.org",
   ]
   ```

2. **Verify Frontend Token Transmission**
   ```javascript
   // Ensure CSRF token is being sent
   customHeaders: {
       'X-CSRFToken': getCSRFToken('csrftoken')
   }
   ```

3. **Check Cookie Settings**
   ```python
   # Ensure cookies are properly configured
   CSRF_COOKIE_DOMAIN = ".cinemata.org"
   CSRF_COOKIE_SECURE = True
   ```

### Upload Size Limits

Adjust upload limits based on your needs:

```nginx
# Nginx configuration
client_max_body_size 2G;  # For 2GB uploads
```

```python
# Django settings
UPLOAD_MAX_SIZE = 2 * 1024 * 1024 * 1024  # 2GB in bytes
```

### CORS Issues

CORS is now handled entirely by Django middleware instead of nginx. If you encounter CORS issues:

1. **Verify Django CORS Headers Middleware is installed and configured**:
   ```python
   # Ensure corsheaders is in MIDDLEWARE (should be first)
   MIDDLEWARE = [
       "corsheaders.middleware.CorsMiddleware",
       # ... other middleware
   ]
   ```

2. **Check CORS Origins Configuration**:
   ```python
   # In settings.py - Configure allowed origins
   CORS_ALLOWED_ORIGINS = [
       "https://cinemata.org",
       "https://www.cinemata.org",
       "https://upload.cinemata.org",
   ]

   # Ensure credentials are allowed
   CORS_ALLOW_CREDENTIALS = True
   ```

3. **Remove any nginx CORS headers** (if migrating from nginx CORS):
   ```nginx
   # These should NOT be present in nginx configuration anymore:
   # add_header Access-Control-Allow-Origin *;
   # add_header Access-Control-Allow-Methods GET, POST, OPTIONS;
   # add_header Access-Control-Allow-Headers DNT,User-Agent,X-Requested-With;
   ```

4. **For development environments, you can use**:
   ```python
   # For development, you can use:
   # CORS_ORIGIN_ALLOW_ALL = True
   ```

## Development vs Production

### Development Environment

```python
# Development settings
DEBUG = True
UPLOAD_SUBDOMAIN = "localhost:8000"
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
```

### Production Environment

```python
# Production settings
DEBUG = False
UPLOAD_SUBDOMAIN = "upload.cinemata.org"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Benefits

1. **Separation of Concerns**: Upload operations are isolated from the main site
2. **Performance**: Upload-specific optimizations without affecting the main site
3. **Security**: CORS and CSRF protection for secure file uploads
4. **Scalability**: Can be scaled independently or moved to a different server
5. **Monitoring**: Separate logging and health monitoring for upload operations

## URL Structure

- Main site: `https://cinemata.org/`
- Upload endpoint: `https://upload.cinemata.org/fu/upload/`
- Health check: `https://upload.cinemata.org/health`
- All other URLs on upload subdomain redirect to main domain

## Additional Security Resources

- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP File Upload Security](https://owasp.org/www-community/vulnerabilities/Unrestricted_File_Upload)
- [Nginx Security Headers](https://nginx.org/en/docs/http/ngx_http_headers_module.html)
- [CORS Security Best Practices](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
