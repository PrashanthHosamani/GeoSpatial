from django.urls import path
from . import views

urlpatterns = [
    path('files/', views.UploadGeoFileAPIView.as_view(), name='file-upload'),
    path('files/list/', views.GeoFileListAPIView.as_view(), name='file-list'),
    path('files/<uuid:id>/', views.GeoFileDetailAPIView.as_view(), name='file-detail'),
    path('files/<uuid:file_id>/measurements/', views.FeatureMeasurementAPIView.as_view(), name='file-measurements'),
]
