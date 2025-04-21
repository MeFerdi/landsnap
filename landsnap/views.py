import time
import uuid
import os
from venv import logger
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views.generic import View, DetailView, ListView, TemplateView
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.urls import reverse
from django.db import transaction
from .forms import UploadForm
from .models import ImageUpload, AnalysisResult
from .utils.image_utils import generate_heatmap, calculate_changes
from .utils.validators import validate_image_dimensions, validate_image_extension, validate_image_size
import logging

logger = logging.getLogger(__name__)

class UploadView(View):
    logger = logging.getLogger(__name__)

class UploadView(View):
    template_name = 'landsnap/upload.html'

    def get_client_ip(self, request):
        """
        Get the client's IP address from the request object
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get(self, request, *args, **kwargs):
        form = UploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = UploadForm(request.POST, request.FILES)
        
        if not form.is_valid():
            errors = {field: error[0] for field, error in form.errors.items()}
            logger.warning(f"Form validation failed: {errors}")
            return JsonResponse({
                'error': 'Form validation failed',
                'errors': errors
            }, status=400)

        try:
            with transaction.atomic():
                
                # Save upload with IP address
                upload = form.save(commit=False)
                upload.ip_address = self.get_client_ip(request)
                upload.result_id = uuid.uuid4()
                upload.save()
                logger.info(f"Created upload instance: {upload.id}")

                result = AnalysisResult.objects.create(
                    upload=upload,
                    status='PROCESSING'
                )
                logger.info(f"Created analysis result: {result.id}")

                try:
                    self.process_images_async(upload.id)
                    logger.info(f"Started processing for upload {upload.id}")
                except Exception as e:
                    logger.error(f"Failed to start processing: {str(e)}")
                    raise

                return JsonResponse({
                    'redirect_url': reverse(
                        'landsnap:processing', 
                        kwargs={'result_id': str(upload.result_id)}
                    )
                })

        except ValidationError as e:
            logger.warning(f"Validation error: {str(e)}")
            return JsonResponse({
                'error': str(e),
                'type': 'validation_error'
            }, status=400)
        except Exception as e:
            logger.exception("Unexpected error during upload processing")
            return JsonResponse({
                'error': str(e) if settings.DEBUG else 'An unexpected error occurred',
                'type': 'server_error'
            }, status=500)

    def process_images_async(self, upload_id):
        """Process images with comprehensive error handling"""
        try:
            upload = ImageUpload.objects.get(id=upload_id)
            result = upload.analysis_result
            result.change_percentage = calculate_changes(upload.image1.path, upload.image2.path) or 0.0
            result.save()
            
            logger.info(f"Starting image processing for upload {upload_id}")
            
            for img_field in ['image1', 'image2']:
                img_path = getattr(upload, img_field).path
                if not os.path.exists(img_path):
                    raise FileNotFoundError(f"{img_field} not found at {img_path}")
                logger.debug(f"{img_field} exists at {img_path}")

            start_time = time.time()
            
            try:
                heatmap = generate_heatmap(upload.image1.path, upload.image2.path)
                change_percentage = calculate_changes(upload.image1.path, upload.image2.path)
            except Exception as e:
                raise RuntimeError(f"Image processing failed: {str(e)}")

            processing_time = round(time.time() - start_time, 2)
            
            result.heatmap = heatmap
            result.change_percentage = change_percentage
            result.processing_time = processing_time
            result.status = 'COMPLETE'
            result.save()
            
            logger.info(f"Successfully processed upload {upload_id} in {processing_time}s")

        except Exception as e:
            logger.exception(f"Image processing failed for upload {upload_id}")
            if 'result' in locals():
                result.status = 'FAILED'
                result.error_message = str(e)
                result.save()
            raise 
class ProcessingView(TemplateView):
    template_name = 'landsnap/processing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['result_id'] = self.kwargs.get('result_id')
        return context
    
from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class AnalysisProgressView(View):
    def get(self, request, result_id):
        """
        Endpoint to check analysis progress
        GET /progress/<uuid:result_id>/
        Returns JSON with status and progress
        """
        try:
            
            upload = get_object_or_404(ImageUpload, result_id=result_id)
            
            result = upload.analysis_result  
            
            response_data = {
                'status': result.status,
                'progress': self.calculate_progress(result.status),
            }
            
            if result.status == 'COMPLETE':
                response_data.update({
                    'redirect_url': reverse(
                        'landsnap:analysis_result',
                        kwargs={'result_id': str(result_id)}
                    ),
                    'change_percentage': result.change_percentage,
                    'processing_time': result.processing_time
                })
            elif result.status == 'FAILED':
                response_data['error'] = result.error_message
            
            return JsonResponse(response_data)
            
        except Exception as e:
            logger.error(f"Progress check failed for {result_id}: {str(e)}")
            return JsonResponse({
                'error': str(e) if settings.DEBUG else 'Analysis status unavailable',
                'status': 'ERROR'
            }, status=500)

    def calculate_progress(self, status):
        """Calculate progress percentage based on analysis status"""
        PROGRESS_MAP = {
            'PENDING': 10,
            'PROCESSING': 50,
            'COMPLETE': 100,
            'FAILED': 100,
            'ERROR': 0
        }
        return PROGRESS_MAP.get(status, 0)

    def calculate_progress(self, status):
        """Simple progress estimation based on status"""
        progress_map = {
            'PENDING': 10,
            'PROCESSING': 50,
            'COMPLETE': 100,
            'FAILED': 100
        }
        return progress_map.get(status, 0)
class ResultsListView(ListView):
    model = AnalysisResult
    template_name = 'landsnap/result.html'
    context_object_name = 'results'
    ordering = ['-created_at']

    def get_queryset(self):
        return AnalysisResult.objects.filter(status='COMPLETE')

class AboutView(TemplateView):
    template_name = 'landsnap/about.html'

class AnalysisResultView(DetailView):
    template_name = 'landsnap/result.html'
    context_object_name = 'result'

    def get_object(self, queryset=None):
        result_id = self.kwargs.get('result_id')
        return get_object_or_404(
            AnalysisResult,
            upload__result_id=result_id
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = context['result']
        
        context.update({
            'change_intensity': self.get_change_intensity(result.change_percentage),
            'processing_efficiency': self.get_processing_efficiency(result.processing_time),
        })
        return context

    def get_change_intensity(self, percentage):
        """Categorize change percentage for display"""
        if percentage < 5:
            return 'Minimal'
        elif percentage < 20:
            return 'Moderate'
        elif percentage < 50:
            return 'Significant'
        return 'Dramatic'

    def get_processing_efficiency(self, seconds):
        """Categorize processing time"""
        if seconds < 5:
            return 'Fast'
        elif seconds < 15:
            return 'Moderate'
        return 'Slow'