from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid

def upload_to(instance, filename):
    """Organize uploads by date and model type"""
    prefix = 'before_after' if isinstance(instance, ImageUpload) else 'results'
    return f"{prefix}/{timezone.now().strftime('%Y/%m/%d')}/{uuid.uuid4().hex[:8]}_{filename}"

class ImageUpload(models.Model):
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PROCESSING', _('Processing')),
        ('COMPLETED', _('Completed')),
        ('FAILED', _('Failed')),
    ]
    
    image1 = models.ImageField(
        upload_to=upload_to,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        verbose_name=_('Before Image'),
        help_text=_('Upload the earlier image of the location')
    )
    image2 = models.ImageField(
        upload_to=upload_to,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        verbose_name=_('After Image'),
        help_text=_('Upload the more recent image of the location')
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Uploaded At'))
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name=_('IP Address'),
        help_text=_('IP address of the uploader')
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name=_('Processing Status')
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Error Message')
    )
    result_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_('Result ID')
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = _("Image Upload")
        verbose_name_plural = _("Image Uploads")
        indexes = [
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Upload #{self.id} ({self.get_status_display()})"

    @property
    def is_processed(self):
        return self.status == 'COMPLETED'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('analysis_result', kwargs={'result_id': str(self.result_id)})


class AnalysisResult(models.Model):
    QUALITY_CHOICES = [
        ('LOW', _('Low Confidence')),
        ('MEDIUM', _('Medium Confidence')),
        ('HIGH', _('High Confidence')),
    ]
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PROCESSING', 'Processing'),
            ('COMPLETE', 'Complete'),
            ('FAILED', 'Failed'),
        ],
        default='PENDING',
    )
    
    upload = models.OneToOneField(
        ImageUpload,
        on_delete=models.CASCADE,
        related_name='analysis_result',
        verbose_name=_('Original Upload')
    )
    heatmap = models.ImageField(
        upload_to=upload_to,
        verbose_name=_('Heatmap Image'),
        help_text=_('Generated change detection heatmap')
    )
    change_percentage = models.FloatField(null=True, blank=True)  
    # change_percentage = models.FloatField(
    #     validators=[MinValueValidator(0), MaxValueValidator(100)],
    #     verbose_name=_('Change Percentage'),
    #     help_text=_('Percentage of area changed (0-100)')
    # )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    processing_time = models.FloatField(null=True, blank=True)
     
    quality_rating = models.CharField(
        max_length=10,
        choices=QUALITY_CHOICES,
        default='MEDIUM',
        verbose_name=_('Quality Rating'),
        help_text=_('Confidence level in the analysis results')
    )
    metadata = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Additional Metadata'),
        help_text=_('Extra analysis data in JSON format')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Analysis Result")
        verbose_name_plural = _("Analysis Results")
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['change_percentage']),
            models.Index(fields=['quality_rating']),
        ]

    def __str__(self):
        return f"Analysis for Upload #{self.upload.id} ({self.change_percentage}% change)"

    @property
    def change_intensity(self):
        """Categorize change percentage for display"""
        if self.change_percentage < 5:
            return _('Minimal')
        elif self.change_percentage < 20:
            return _('Moderate')
        elif self.change_percentage < 50:
            return _('Significant')
        return _('Dramatic')

    def get_absolute_url(self):
        return self.upload.get_absolute_url()