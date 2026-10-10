import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point
import zipfile
import os

# Create geometries: Polygons
geometries = [
    Polygon([(-122.0, 37.0), (-121.9, 37.0), (-121.9, 37.1), (-122.0, 37.1), (-122.0, 37.0)]),
    Polygon([(-121.8, 37.0), (-121.7, 37.0), (-121.7, 37.1), (-121.8, 37.1), (-121.8, 37.0)])
]

# Create a GeoDataFrame without string columns to avoid dtype interpretation issues
gdf = gpd.GeoDataFrame({
    'geometry': geometries
}, crs="EPSG:4326")

# Save as Shapefile
output_dir = "mixed_shapefile"
os.makedirs(output_dir, exist_ok=True)
shapefile_path = os.path.join(output_dir, "mixed_data.shp")
gdf.to_file(shapefile_path)

# Zip the shapefile components (.shp, .shx, .dbf, .prj, .cpg)
with zipfile.ZipFile("mixed_features.zip", "w") as zf:
    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
        file_path = os.path.join(output_dir, f"mixed_data{ext}")
        if os.path.exists(file_path):
            zf.write(file_path, arcname=f"mixed_data{ext}")

print("Successfully created mixed_features.zip")
