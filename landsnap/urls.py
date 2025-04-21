from django.urls import path
from .views import UploadView, AnalysisResultView, AnalysisProgressView, AboutView, ResultsListView

app_name = 'landsnap'

urlpatterns = [
    path('', UploadView.as_view(), name='upload'),
    path('results/', ResultsListView.as_view(), name='results'),
    path('results/<uuid:result_id>/', AnalysisResultView.as_view(), name='analysis_result'),
    path('api/analysis-progress/', AnalysisProgressView.as_view(), name='analysis_progress'),
    path('about/', AboutView.as_view(), name='about'),
]