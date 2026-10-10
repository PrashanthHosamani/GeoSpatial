import logging 
from celery import shared_task
from django.utils import timezone
from django.contrib.gis.geos import GEOSGeometry
from .models import GeoFile, Feature
from geo_spatial.services.file_parser import FileParser
from geo_spatial.services.crs_handler import CRSHandler
from geo_spatial.services.measurement import MeasurementCalculator
import pandas as pd
import shapely
import pyproj

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_geo_file(self, geo_file_id: str):
    try:
        geo_file = GeoFile.objects.get(id=geo_file_id)
        geo_file.status = GeoFile.Status.PROCESSING
        geo_file.save()

        parser = FileParser()
        gdf = parser.parse(geo_file.file.path)

        try:
            if gdf.crs:
                pyproj.CRS(gdf.crs)
        except Exception:
            gdf.set_crs("EPSG:4326", allow_override=True, inplace=True)

        if getattr(gdf, 'has_z', None) is not None and gdf.has_z.any():
            gdf.geometry = gdf.geometry.apply(lambda g: shapely.force_2d(g) if g and getattr(g, 'has_z', False) else g)

        crs_handler = CRSHandler()
        original_crs = crs_handler.get_crs_string(gdf)
        if original_crs and len(original_crs) > 40:
            original_crs = "Custom Projection"
            
        projected_gdf, projected_crs = crs_handler.transform_to_projected(gdf)
        if projected_crs and len(projected_crs) > 40:
            projected_crs = "Custom Projection"

        calculator = MeasurementCalculator()
        measurements = calculator.calculate(projected_gdf)

        if gdf.crs and crs_handler.get_crs_string(gdf) != "EPSG:4326":
            try:
                gdf_wgs84 = gdf.to_crs("EPSG:4326")
            except Exception:
                gdf_wgs84 = gdf
        else:
            gdf_wgs84 = gdf

        features_to_create = []
        batch_size = 1000
        total_created = 0

        for i, (idx, row) in enumerate(gdf_wgs84.iterrows()):
            properties = {}
            for col in gdf_wgs84.columns:
                if col != 'geometry':
                    val = row[col]
                    if pd.isna(val):
                        val = None
                    properties[col] = str(val) if not isinstance(val, (int, float, str, bool, type(None))) else val

            geom = GEOSGeometry(row.geometry.wkb_hex, srid=4326) if row.geometry else None
            m = measurements[i]

            feature = Feature(
                geo_file=geo_file,
                feature_index=i,
                geometry_type=row.geometry.geom_type if row.geometry else 'Unknown',
                geometry=geom,
                properties=properties,
                area_sqm=m['area_sqm'],
                length_m=m['length_m'],
                projected_crs=projected_crs,
            )
            features_to_create.append(feature)

            if len(features_to_create) >= batch_size:
                Feature.objects.bulk_create(features_to_create)
                total_created += len(features_to_create)
                features_to_create = []

        if features_to_create:
            Feature.objects.bulk_create(features_to_create)
            total_created += len(features_to_create)

        geo_file.original_crs = original_crs
        geo_file.feature_count = total_created
        geo_file.status = GeoFile.Status.COMPLETED
        geo_file.processed_at = timezone.now()
        geo_file.save()

        logger.info(f"Successfully processed {geo_file.filename}: {total_created} features")

    except GeoFile.DoesNotExist:
        logger.error(f"GeoFile {geo_file_id} not found")
    except Exception as exc:
        logger.error(f"Error processing file {geo_file_id}: {exc}", exc_info=True)
        try:
            geo_file = GeoFile.objects.get(id=geo_file_id)
            geo_file.status = GeoFile.Status.FAILED
            geo_file.error_message = str(exc)
            geo_file.save()
        except GeoFile.DoesNotExist:
            pass