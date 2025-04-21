from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ImageUpload, AnalysisResult

@admin.register(ImageUpload)
class ImageUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_at', 'image1_preview', 'image2_preview', 'ip_address', 'analysis_link')
    readonly_fields = ('uploaded_at', 'ip_address', 'image1_preview', 'image2_preview')
    list_filter = ('uploaded_at',)
    search_fields = ('ip_address',)
    date_hierarchy = 'uploaded_at'
    fieldsets = (
        (None, {
            'fields': ('image1', 'image1_preview', 'image2', 'image2_preview')
        }),
        ('Metadata', {
            'fields': ('uploaded_at', 'ip_address'),
            'classes': ('collapse',)
        }),
    )

    def image1_preview(self, obj):
        if obj.image1:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image1.url)
        return "-"
    image1_preview.short_description = 'Before Image Preview'

    def image2_preview(self, obj):
        if obj.image2:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image2.url)
        return "-"
    image2_preview.short_description = 'After Image Preview'

    def analysis_link(self, obj):
        if hasattr(obj, 'analysisresult'):
            url = reverse('admin:landsnap_analysisresult_change', args=[obj.analysisresult.id])
            return format_html('<a href="{}">View Analysis</a>', url)
        return "Not processed"
    analysis_link.short_description = 'Analysis'
    analysis_link.allow_tags = True

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'upload_link', 'change_percentage', 'processing_time', 'created_at', 'heatmap_preview')
    readonly_fields = ('created_at', 'heatmap_preview', 'change_percentage', 'processing_time', 'upload_link')
    list_filter = ('created_at', 'change_percentage')
    search_fields = ('upload__id',)
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Results', {
            'fields': ('upload_link', 'heatmap_preview', 'change_percentage', 'processing_time')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def heatmap_preview(self, obj):
        if obj.heatmap:
            return format_html('<img src="{}" style="max-height: 200px; max-width: 200px;" />', obj.heatmap.url)
        return "-"
    heatmap_preview.short_description = 'Heatmap Preview'

    def upload_link(self, obj):
        url = reverse('admin:landsnap_imageupload_change', args=[obj.upload.id])
        return format_html('<a href="{}">Upload #{}</a>', url, obj.upload.id)
    upload_link.short_description = 'Original Upload'
    upload_link.allow_tags = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('upload')