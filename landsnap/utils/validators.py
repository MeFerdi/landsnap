from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from PIL import Image
import os

MAX_FILE_SIZE = 10 * 1024 * 1024
MIN_DIMENSION = 500

def validate_image_size(image):
    """Validate that image size is within acceptable limits"""
    if image.size > MAX_FILE_SIZE:
        raise ValidationError(
            _('Image size must be less than %(max_size)sMB.'),
            params={'max_size': MAX_FILE_SIZE // (1024 * 1024)},
            code='image_too_large'
        )

def validate_image_dimensions(image):
    """Validate that image meets minimum dimension requirements"""
    try:
        with Image.open(image) as img:
            width, height = img.size
            if width < MIN_DIMENSION or height < MIN_DIMENSION:
                raise ValidationError(
                    _('Image dimensions must be at least %(min_dim)s pixels in both width and height.'),
                    params={'min_dim': MIN_DIMENSION},
                    code='image_too_small'
                )
            
            # Additional validations could include:
            # - Aspect ratio checks
            # - Color mode validation
    except Exception as e:
        raise ValidationError(
            _('Unable to validate image dimensions: %(error)s'),
            params={'error': str(e)},
            code='image_invalid'
        )

def validate_image_extension(image):
    """Validate file extension (though accept attribute in form should handle this)"""
    ext = os.path.splitext(image.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if ext not in valid_extensions:
        raise ValidationError(
            _('Unsupported file extension. Only JPG and PNG are allowed.'),
            code='invalid_extension'
        )