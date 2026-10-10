import geopandas as gpd
from pyproj import CRS
from shapely.geometry import shape

class CRSHandler:
    
    def get_crs_string(self, gdf: gpd.GeoDataFrame) -> str:
        if gdf.crs is None:
            return "EPSG:4326"
        
        epsg = gdf.crs.to_epsg()
        if epsg:
            return f"EPSG:{epsg}"
        return str(gdf.crs)

    def is_geographic(self, gdf: gpd.GeoDataFrame) -> bool:
        if gdf.crs:
            return CRS(gdf.crs).is_geographic
        return True

    def get_utm_epsg(self, longitude: float, latitude: float) -> int:
        utm_zone = int((longitude + 180) / 6) + 1
        if latitude >= 0:
            return 32600 + utm_zone
        else:
            return 32700 + utm_zone

    def transform_to_projected(self, gdf: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, str]:
        if not self.is_geographic(gdf):
            return gdf, self.get_crs_string(gdf)
            
        centroid = gdf.geometry.unary_union.centroid
        utm_epsg = self.get_utm_epsg(centroid.x, centroid.y)
        projected_gdf = gdf.to_crs(epsg=utm_epsg)
        return projected_gdf, f"EPSG:{utm_epsg}"
