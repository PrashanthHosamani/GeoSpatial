from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from .models import GeoFile, Feature
from .serializers import GeoFileSerializer, GeoFileDetailSerializer, FeatureMeasurementSerializer
from .tasks import process_geo_file

class UploadGeoFileAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = GeoFileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(filename=request.FILES['file'].name)
            process_geo_file.delay(str(serializer.instance.id))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GeoFileListAPIView(generics.ListAPIView):
    queryset = GeoFile.objects.all().order_by('-uploaded_at')
    serializer_class = GeoFileDetailSerializer

class GeoFileDetailAPIView(generics.RetrieveAPIView):
    queryset = GeoFile.objects.all()
    serializer_class = GeoFileDetailSerializer
    lookup_field = 'id'

class FeatureMeasurementAPIView(generics.ListAPIView):
    serializer_class = FeatureMeasurementSerializer

    def get_queryset(self):
        file_id = self.kwargs.get('file_id')
        return Feature.objects.filter(geo_file_id=file_id)