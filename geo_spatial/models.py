from django.db.models import CharField
import uuid
from django.contrib.gis.db import models as gis_models
from django.db import models

class GeoFile(models.Model):

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'

    id = models.UUIDField(primary_key = True, default = uuid.uuid4)
    filename = CharField(max_length = 255)
    original_crs = CharField(max_length = 255, blank = True, null = True)
    feature_count = models.IntegerField(null = True, blank = True)
    status = models.CharField(max_length = 50, choices = Status.choices, default = 'Pending')
    file = models.FileField(upload_to = 'uploads/')
    uploaded_at = models.DateTimeField(auto_now_add =True)
    processed_at = models.DateTimeField(null = True, blank = True)
    error_message = models.TextField(max_length = 1000, blank = True, null = True)

    class Meta:
        db_table = 'GeoFiles'
        verbose_name = 'GeoFiles'
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.filename

class Feature(models.Model):
    id = models.UUIDField(primary_key = True, default = uuid.uuid4, editable = False)
    geo_file = models.ForeignKey(GeoFile, on_delete = models.CASCADE, related_name = 'features')
    feature_index = models.IntegerField(null = True, blank = True)
    geometry = gis_models.GeometryField(null = True, blank = True)
    geometry_type = CharField(max_length = 50, blank = True, null = True)
    properties = models.JSONField(default = dict, blank = True)
    area_sqm = models.FloatField(null = True, blank = True)
    length_m = models.FloatField(null = True, blank = True)
    projected_crs = CharField(max_length = 100, null = True, blank = True)

    class Meta:
        db_table = 'Feature'
        ordering = ['feature_index']

    def __str__(self):
        return f"Feature {self.feature_index} from {self.geo_file.filename}"

    
    



