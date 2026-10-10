import geopandas as gpd

class MeasurementCalculator:

    AREA_TYPES = ['Polygon', 'MultiPolygon']
    LENGTH_TYPES = ['LineString', 'MultiLineString']

    def calculate(self, projected_gdf: gpd.GeoDataFrame) -> list[dict]:
        results = []
        for idx, row in projected_gdf.iterrows():
            geom_type = row.geometry.geom_type if row.geometry else 'Unknown'
            
            measurement = {
                'feature_index': idx,
                'geometry_type': geom_type,
                'area_sqm': None,
                'length_m': None,
            }

            if row.geometry and geom_type in self.AREA_TYPES:
                measurement['area_sqm'] = round(row.geometry.area, 4)
            elif row.geometry and geom_type in self.LENGTH_TYPES:
                measurement['length_m'] = round(row.geometry.length, 4)

            results.append(measurement)

        return results
