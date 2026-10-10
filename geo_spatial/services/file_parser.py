import os
from zipfile import ZipFile
import tempfile
import geopandas as gpd 
import fiona
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

    def _parse_kml(self, kml_path: str) -> gpd.GeoDataFrame:
        layers = fiona.listlayers(kml_path)
        if not layers:
            raise ValueError("No layers found in the KML file")
            
        dataframes = []
        for layer_name in layers:
            gdf = gpd.read_file(kml_path, driver='KML', layer=layer_name)
            dataframes.append(gdf)
            
        return pd.concat(dataframes, ignore_index=True)
