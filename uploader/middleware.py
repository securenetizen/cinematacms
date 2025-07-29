"""
Custom CORS middleware for file uploads with credentials support.
This middleware handles cross-origin requests for the upload endpoints,
supporting multiple domains and credentials (cookies, authentication headers).
"""

from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin


class UploadCorsMiddleware(MiddlewareMixin):
    """
    Custom CORS middleware for upload endpoints that supports credentials.

    This middleware:
    - Handles OPTIONS preflight requests
    - Sets appropriate CORS headers for upload endpoints
    - Supports multiple allowed origins with credentials
    - Only applies to upload-related URLs (/fu/ paths)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        """Handle OPTIONS preflight requests for upload endpoints"""
        if request.method == 'OPTIONS' and request.path.startswith('/fu/'):
            return self._handle_preflight(request)
        return None

    def process_response(self, request, response):
        """Add CORS headers to upload endpoint responses"""
        if request.path.startswith('/fu/'):
            return self._add_cors_headers(request, response)
        return response

    def _handle_preflight(self, request):
        """Handle OPTIONS preflight requests"""
        response = HttpResponse()
        response = self._add_cors_headers(request, response)
        response['Access-Control-Max-Age'] = '1728000'  # 20 days
        response['Content-Length'] = '0'
        return response

    def _add_cors_headers(self, request, response):
        """Add CORS headers to response"""
        origin = request.META.get('HTTP_ORIGIN', '')

        # Get allowed origins from settings
        main_domains = getattr(settings, 'MAIN_DOMAINS', [])
        upload_domains = getattr(settings, 'UPLOAD_DOMAINS', [])
        allowed_origins = main_domains + upload_domains

        # Check if origin is allowed
        if origin in allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
        else:
            # Fallback for development - allow localhost variations
            if any(domain in origin for domain in ['localhost', '127.0.0.1']) and settings.DEBUG:
                response['Access-Control-Allow-Origin'] = origin
                response['Access-Control-Allow-Credentials'] = 'true'

        # Set other CORS headers
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = (
            'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,'
            'Content-Type,Range,X-CSRFToken,Authorization'
        )
        response['Access-Control-Expose-Headers'] = 'Content-Length,Content-Range'

        return response