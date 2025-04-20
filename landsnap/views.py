import time
from django.shortcuts import render, redirect
from django.views.generic import DetailView
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseForbidden
from .forms import UploadForm
from .models import ImageUpload, AnalysisResult
from .utils.image_utils import generate_heatmap, calculate_changes
from .utils.validators import validate_image_size

class UploadView(DetailView):
    template_name = 'landsnap/upload.html'

    def get(self, request, *args, **kwargs):
        form = UploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = UploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        try:
            # Validate images before saving
            validate_image_size(request.FILES['image1'])
            validate_image_size(request.FILES['image2'])
            
            # Save upload with IP logging
            upload = form.save(commit=False)
            upload.ip_address = request.META.get('REMOTE_ADDR')
            upload.save()

            # Process images
            start_time = time.time()
            heatmap = generate_heatmap(upload.image1.path, upload.image2.path)
            change_percentage = calculate_changes(upload.image1.path, upload.image2.path)
            processing_time = round(time.time() - start_time, 2)

            # Save results
            AnalysisResult.objects.create(
                upload=upload,
                heatmap=heatmap,
                change_percentage=change_percentage,
                processing_time=processing_time
            )

            return redirect('analysis_result', pk=upload.id)

        except (ValueError, SuspiciousOperation) as e:
            return HttpResponseForbidden(str(e))

class AnalysisResultView(DetailView):
    model = AnalysisResult
    template_name = 'landsnap/result.html'
    context_object_name = 'result'