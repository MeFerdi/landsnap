from django import forms
from .models import ImageUpload
from .utils.validators import validate_image_size

class UploadForm(forms.ModelForm):
    class Meta:
        model = ImageUpload
        fields = ['image1', 'image2']
        widgets = {
            'image1': forms.FileInput(attrs={
                'accept': 'image/jpeg,image/png',
                'class': 'form-control'
            }),
            'image2': forms.FileInput(attrs={
                'accept': 'image/jpeg,image/png',
                'class': 'form-control'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        for field in ['image1', 'image2']:
            if field in cleaned_data:
                validate_image_size(cleaned_data[field])
        return cleaned_data