from django.contrib import admin
from .models import ImageUpload, AnalysisResult

@admin.register(ImageUpload)
class ImageUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    list_filter = ('uploaded_at',)

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'upload', 'change_percentage', 'created_at')
    readonly_fields = ('created_at', 'heatmap', 'change_percentage')
    list_filter = ('created_at',)