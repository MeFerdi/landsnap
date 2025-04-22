from django.urls import path
from .views import DownloadHeatmapView, ProcessingView, UploadView, AnalysisResultView, AnalysisProgressView, AboutView, ResultsListView

app_name = 'landsnap'

urlpatterns = [
    path('', UploadView.as_view(), name='upload'),
    path('results/', ResultsListView.as_view(), name='results'),
    path('results/<uuid:result_id>/', AnalysisResultView.as_view(), name='analysis_result'),
    path('processing/<uuid:result_id>/', ProcessingView.as_view(), name='processing'),
    path('progress/<uuid:result_id>/', AnalysisProgressView.as_view(), name='analysis_progress'),
    path('download/<uuid:result_id>/<str:format>/', DownloadHeatmapView.as_view(), name='download_heatmap'),
    path('about/', AboutView.as_view(), name='about'),
]