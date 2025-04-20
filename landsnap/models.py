from django.db import models
from django.core.validators import FileExtensionValidator

class ImageUpload(models.Model):
    """Stores uploaded image pairs for analysis"""
    image1 = models.ImageField(
        upload_to='uploads/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    image2 = models.ImageField(
        upload_to='uploads/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

class AnalysisResult(models.Model):
    """Stores analysis results"""
    upload = models.OneToOneField(ImageUpload, on_delete=models.CASCADE)
    heatmap = models.ImageField(upload_to='results/%Y/%m/%d/')
    change_percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis #{self.id}"