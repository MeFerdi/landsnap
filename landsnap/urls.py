from django.urls import path
from .views import UploadView, AnalysisResultView

app_name = 'landsnap'

urlpatterns = [
    path('', UploadView.as_view(), name='upload'),
    path('result/<int:pk>/', AnalysisResultView.as_view(), name='analysis_result'),
]