from django.contrib.gis import admin
from .models import GeoFile, Feature

class GeoFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'filename', 'status', 'feature_count')
    list_filter = ('status', 'uploaded_at')
    search_fields = ('filename',)
    readonly_fields = ('uploaded_at',)

class FeatureAdmin(admin.ModelAdmin):
    list_display = ('feature_index', 'geometry_type', 'geo_file')
    list_filter = ('geometry_type',)
    search_fields = ('geo_file__filename',)
    readonly_fields = ('feature_index',)

admin.site.register(GeoFile, GeoFileAdmin)
admin.site.register(Feature, FeatureAdmin)