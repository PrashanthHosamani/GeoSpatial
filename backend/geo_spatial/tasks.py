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
        crs_handler = CRSHandler()
        calculator = MeasurementCalculator()

        total_created = 0
        original_crs = None
        final_projected_crs = None

        for gdf_chunk in parser.parse_in_chunks(geo_file.file.path, chunk_size=2000):
            try:
                if gdf_chunk.crs:
                    pyproj.CRS(gdf_chunk.crs)
            except Exception:
                gdf_chunk.set_crs("EPSG:4326", allow_override=True, inplace=True)

            if getattr(gdf_chunk, 'has_z', None) is not None and gdf_chunk.has_z.any():
                gdf_chunk.geometry = gdf_chunk.geometry.apply(lambda g: shapely.force_2d(g) if g and getattr(g, 'has_z', False) else g)

            chunk_orig_crs = crs_handler.get_crs_string(gdf_chunk)
            if not original_crs:
                original_crs = chunk_orig_crs
                if original_crs and len(original_crs) > 40:
                    original_crs = "Custom Projection"
                
            projected_gdf, projected_crs = crs_handler.transform_to_projected(gdf_chunk)
            if not final_projected_crs:
                final_projected_crs = projected_crs
                if final_projected_crs and len(final_projected_crs) > 40:
                    final_projected_crs = "Custom Projection"

            measurements = calculator.calculate(projected_gdf)

            if gdf_chunk.crs and crs_handler.get_crs_string(gdf_chunk) != "EPSG:4326":
                try:
                    gdf_wgs84 = gdf_chunk.to_crs("EPSG:4326")
                except Exception:
                    gdf_wgs84 = gdf_chunk
            else:
                gdf_wgs84 = gdf_chunk

            features_to_create = []
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
                    feature_index=total_created + i,
                    geometry_type=row.geometry.geom_type if row.geometry else 'Unknown',
                    geometry=geom,
                    properties=properties,
                    area_sqm=m['area_sqm'],
                    length_m=m['length_m'],
                    projected_crs=final_projected_crs,
                )
                features_to_create.append(feature)

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