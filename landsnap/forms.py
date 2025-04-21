from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ImageUpload
from .utils.validators import validate_image_size, validate_image_dimensions

class UploadForm(forms.ModelForm):
    # Add explicit field definitions for more control
    image1 = forms.ImageField(
        label=_('Before Image'),
        help_text=_('Upload the earlier image of the location'),
        widget=forms.FileInput(attrs={
            'accept': 'image/jpeg,image/png',
            'class': 'form-control',
            'aria-describedby': 'image1Help'
        })
    )
    
    image2 = forms.ImageField(
        label=_('After Image'),
        help_text=_('Upload the more recent image of the location'),
        widget=forms.FileInput(attrs={
            'accept': 'image/jpeg,image/png',
            'class': 'form-control',
            'aria-describedby': 'image2Help'
        })
    )

    class Meta:
        model = ImageUpload
        fields = ['image1', 'image2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap form-control class to all fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        image1 = cleaned_data.get('image1')
        image2 = cleaned_data.get('image2')
        
        # Validate each image individually
        for field_name, image in [('image1', image1), ('image2', image2)]:
            if image:
                try:
                    validate_image_size(image)
                    validate_image_dimensions(image)
                except forms.ValidationError as e:
                    self.add_error(field_name, e)
        
        # Additional validation that requires both images
        if image1 and image2:
            self._validate_image_pair(image1, image2)
        
        return cleaned_data

    def _validate_image_pair(self, image1, image2):
        """
        Validate that the two images are suitable for comparison
        """
        # Check if images are too different in size
        size_ratio = image1.size / image2.size
        if size_ratio > 2 or size_ratio < 0.5:
            raise forms.ValidationError(
                _("The images are too different in file size. They should be similar in resolution."),
                code='image_size_mismatch'
            )