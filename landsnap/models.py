from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone

def upload_to(instance, filename):
    return f"uploads/{timezone.now().strftime('%Y/%m/%d')}/{filename}"

class ImageUpload(models.Model):
    image1 = models.ImageField(
        upload_to=upload_to,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    image2 = models.ImageField(
        upload_to=upload_to,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Image Upload"
        verbose_name_plural = "Image Uploads"

    def __str__(self):
        return f"Upload #{self.id}"

class AnalysisResult(models.Model):
    upload = models.OneToOneField(
        ImageUpload,
        on_delete=models.CASCADE,
        related_name='analysis_result'
    )
    heatmap = models.ImageField(upload_to='results/')
    change_percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    processing_time = models.FloatField(help_text="Processing time in seconds")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Analysis Result"
        verbose_name_plural = "Analysis Results"

    def __str__(self):
        return f"Analysis for Upload #{self.upload.id}"