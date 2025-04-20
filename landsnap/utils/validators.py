from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MAX_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png']

def validate_image_size(image):
    """Validate image size and type"""
    if image.size > MAX_UPLOAD_SIZE:
        raise ValidationError(
            _('Image size exceeds maximum allowed size of %(max_size)sMB'),
            params={'max_size': MAX_UPLOAD_SIZE // (1024 * 1024)},
        )
    
    if image.content_type not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            _('Unsupported image type. Only JPEG and PNG are allowed.')
        )