import time
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, DetailView, ListView, TemplateView
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.http import JsonResponse
from django.urls import reverse
from django.db import transaction
from .forms import UploadForm
from .models import ImageUpload, AnalysisResult
from .utils.image_utils import generate_heatmap, calculate_changes
from .utils.validators import validate_image_size

class UploadView(View):
    template_name = 'landsnap/upload.html'

    def get(self, request, *args, **kwargs):
        form = UploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = UploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        try:
            with transaction.atomic():
                # Validate images before saving
                validate_image_size(request.FILES['image1'])
                validate_image_size(request.FILES['image2'])
                
                # Save upload with IP logging
                upload = form.save(commit=False)
                upload.ip_address = self.get_client_ip(request)
                upload.result_id = uuid.uuid4()  # Generate unique ID
                upload.save()

                # Create initial result record
                result = AnalysisResult.objects.create(
                    upload=upload,
                    status='PROCESSING'
                )

                # Start async processing (in reality you'd use Celery here)
                self.process_images_async(upload.id)

                return redirect('landsnap:analysis_progress', result_id=upload.result_id)

        except (ValueError, SuspiciousOperation, ValidationError) as e:
            form.add_error(None, str(e))
            return render(request, self.template_name, {'form': form})

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

    def process_images_async(self, upload_id):
        """This would be replaced with Celery task in production"""
        try:
            upload = ImageUpload.objects.get(id=upload_id)
            result = upload.analysisresult
            
            # Process images
            start_time = time.time()
            heatmap = generate_heatmap(upload.image1.path, upload.image2.path)
            change_percentage = calculate_changes(upload.image1.path, upload.image2.path)
            processing_time = round(time.time() - start_time, 2)

            # Update results
            result.heatmap = heatmap
            result.change_percentage = change_percentage
            result.processing_time = processing_time
            result.status = 'COMPLETE'
            result.save()

        except Exception as e:
            result.status = 'FAILED'
            result.error_message = str(e)
            result.save()


class AnalysisProgressView(View):
    def get(self, request, result_id, *args, **kwargs):
        try:
            upload = get_object_or_404(ImageUpload, result_id=result_id)
            result = upload.analysisresult
            
            response_data = {
                'status': result.status,
                'progress': self.calculate_progress(result.status),
            }
            
            if result.status == 'COMPLETE':
                response_data['redirect_url'] = reverse(
                    'landsnap:analysis_result',
                    kwargs={'result_id': str(result_id)}
                )
            elif result.status == 'FAILED':
                response_data['error'] = result.error_message
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

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
        
        # Add additional context data
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