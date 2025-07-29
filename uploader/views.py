# -*- coding: utf-8 -*-
import os
import shutil

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.http import JsonResponse
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator

from cms.permissions import user_allowed_to_upload
from files.helpers import rm_file
from files.models import Media

from .fineuploader import ChunkedFineUploader
from .forms import FineUploaderUploadForm, FineUploaderUploadSuccessForm


class FineUploaderView(generic.FormView):
    http_method_names = ("post",)
    form_class_upload = FineUploaderUploadForm
    form_class_upload_success = FineUploaderUploadSuccessForm

    @property
    def concurrent(self):
        """Enable/disable concurrent chunk uploads based on settings"""
        return settings.CONCURRENT_UPLOADS

    @property
    def chunks_done(self):
        """Check if this is a chunk completion request (final step)"""
        return self.chunks_done_param_name in self.request.GET

    @property
    def chunks_done_param_name(self):
        """Parameter name for chunk completion requests"""
        return settings.CHUNKS_DONE_PARAM_NAME

    def make_response(self, data, **kwargs):
        """
        Create JSON response for upload requests.
        CORS headers are handled by UploadCorsMiddleware.
        """
        return JsonResponse(data, **kwargs)

    def get_form(self, form_class=None):
        """Select appropriate form based on upload stage"""
        if self.chunks_done:
            form_class = self.form_class_upload_success
        else:
            form_class = self.form_class_upload
        return form_class(**self.get_form_kwargs())

    def dispatch(self, request, *args, **kwargs):
        """
        Handle request dispatch with permission and CSRF validation

        Validates:
        - User permission to upload files
        - CSRF token from X-CSRFToken header or csrftoken cookie
        """
        # Check upload permissions
        if not user_allowed_to_upload(request):
            raise PermissionDenied  # HTTP 403

        # Validate CSRF token for cross-origin requests
        csrf_token = request.META.get('HTTP_X_CSRFTOKEN')
        if not csrf_token:
            # Try to get from cookie if header not present
            csrf_token = request.COOKIES.get('csrftoken')

        if not csrf_token:
            return self.make_response(
                {"success": False, "error": "CSRF token missing"},
                status=403
            )

        return super(FineUploaderView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Process valid upload form

        Handles:
        - Single file uploads
        - Chunked file uploads (individual chunks)
        - Chunk combination (final step for chunked uploads)
        - Media object creation upon completion
        """
        self.upload = ChunkedFineUploader(form.cleaned_data, self.concurrent)

        if self.upload.concurrent and self.chunks_done:
            # Final step: combine all chunks into complete file
            try:
                self.upload.combine_chunks()
            except FileNotFoundError:
                return self.make_response(
                    {"success": False, "error": "Error combining file chunks"},
                    status=400
                )
        elif self.upload.total_parts == 1:
            # Single file upload - save directly
            self.upload.save()
        else:
            # Chunked upload - save individual chunk and return success
            self.upload.save()
            return self.make_response({"success": True})

        # Create Media object from completed upload
        media_file = os.path.join(settings.MEDIA_ROOT, self.upload.real_path)
        try:
            with open(media_file, "rb") as f:
                myfile = File(f)
                new = Media.objects.create(media_file=myfile, user=self.request.user)

            # Clean up temporary files
            rm_file(media_file)
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, self.upload.file_path))

            return self.make_response({
                "success": True,
                "media_url": new.get_absolute_url(),
                "message": "File uploaded successfully"
            })
        except Exception as e:
            return self.make_response(
                {"success": False, "error": f"Error creating media object: {str(e)}"},
                status=500
            )

    def form_invalid(self, form):
        """Handle invalid form submission with detailed error response"""
        return self.make_response(
            {"success": False, "error": f"Form validation failed: {repr(form.errors)}"},
            status=400
        )
