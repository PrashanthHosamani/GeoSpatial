import json
from rest_framework import serializers 
import os
from .models import GeoFile, Feature

class GeoFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoFile
        fields = ['id', 'file', 'uploaded_at', 'status', 'filename']
        read_only_fields = ['id', 'uploaded_at', 'status', 'filename']

    def validate_file(self, value):
        allowed_extentions = ['.zip', '.kml']
        _, extention = os.path.splitext(value.name)
        if extention.lower() not in allowed_extentions:
            raise serializers.ValidationError("Unsupported extention, please upload zip or kml only")
        return value 

class GeoFileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoFile
        fields = ['id', 'filename', 'feature_count', 'original_crs', 'status', 'error_message', 'uploaded_at', 'processed_at']

class FeatureMeasurementSerializer(serializers.ModelSerializer):
    geometry = serializers.SerializerMethodField()
    area_sqm = serializers.SerializerMethodField()
    length_m = serializers.SerializerMethodField()

    class Meta:
        model = Feature
        fields = ['id', 'feature_index', 'geometry', 'geometry_type', 'properties', 'area_sqm', 'length_m', 'projected_crs']

    def get_geometry(self, obj):
        if obj.geometry:
            return json.loads(obj.geometry.geojson)
        return None

    def get_area_sqm(self, obj):
        import math
        if obj.area_sqm is not None and math.isnan(obj.area_sqm):
            return None
        return obj.area_sqm

    def get_length_m(self, obj):
        import math
        if obj.length_m is not None and math.isnan(obj.length_m):
            return None
        return obj.length_m
