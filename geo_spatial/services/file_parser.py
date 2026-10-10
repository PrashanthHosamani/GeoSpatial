import os
from zipfile import ZipFile
import tempfile
import geopandas as gpd 
import fiona
fiona.drvsupport.supported_drivers['KML'] = 'rw'
fiona.drvsupport.supported_drivers['libKML'] = 'rw'
fiona.drvsupport.supported_drivers['ESRI Shapefile'] = 'rw'
import pandas as pd


class FileParser:
    
    SUPPORTED_EXTENTIONS = ['.zip', '.kml']

    def parse(self, file_path: str) -> gpd.GeoDataFrame:
        root, extention = os.path.splitext(file_path.lower())
        if extention == '.zip':
            return self._parse_shapefile(file_path)
        elif extention == '.kml':
            return self._parse_kml(file_path)
        else:
            raise ValueError(f"Unsopported file extention {extention} ")

    def parse_in_chunks(self, file_path: str, chunk_size: int = 2000):
        root, extention = os.path.splitext(file_path.lower())
        if extention == '.zip':
            yield from self._parse_shapefile_chunks(file_path, chunk_size)
        elif extention == '.kml':
            gdf = self._parse_kml(file_path)
            for i in range(0, len(gdf), chunk_size):
                yield gdf.iloc[i:i+chunk_size].copy()
        else:
            raise ValueError(f"Unsopported file extention {extention} ")

    def _parse_shapefile(self, zip_path: str) -> gpd.GeoDataFrame:
        with tempfile.TemporaryDirectory() as temp_dir:
            with ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

                shape_file_path = None
                for current_folder, sub_folders, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.shp'):
                            shape_file_path = os.path.join(current_folder, file)
                            break
                    if shape_file_path:
                        break
                
                if not shape_file_path:
                    raise ValueError("No .shp file found in the zip file")

                return gpd.read_file(shape_file_path)

    def _parse_shapefile_chunks(self, zip_path: str, chunk_size: int):
        with tempfile.TemporaryDirectory() as temp_dir:
            with ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

                shape_file_path = None
                for current_folder, sub_folders, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.shp'):
                            shape_file_path = os.path.join(current_folder, file)
                            break
                    if shape_file_path:
                        break
                
                if not shape_file_path:
                    raise ValueError("No .shp file found in the zip file")

                with fiona.open(shape_file_path) as src:
                    total_rows = len(src)
                
                for start in range(0, total_rows, chunk_size):
                    end = min(start + chunk_size, total_rows)
                    yield gpd.read_file(shape_file_path, rows=slice(start, end))

    def _parse_kml(self, kml_path: str) -> gpd.GeoDataFrame:
        layers = fiona.listlayers(kml_path)
        if not layers:
            raise ValueError("No layers found in the KML file")
            
        dataframes = []
        for layer_name in layers:
            gdf = gpd.read_file(kml_path, driver='KML', layer=layer_name)
            dataframes.append(gdf)
            
        return pd.concat(dataframes, ignore_index=True)
