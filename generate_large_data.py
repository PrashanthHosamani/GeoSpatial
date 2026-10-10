import random

with open("large_dataset.kml", "w") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
    f.write('  <Document>\n')
    f.write('    <name>Large Agricultural Grid</name>\n')
    
    # Generate 100 polygons (grid of 10x10)
    base_lon = -122.100
    base_lat = 37.400
    step = 0.005

    for i in range(10):
        for j in range(10):
            lon1 = base_lon + (i * step)
            lat1 = base_lat + (j * step)
            lon2 = lon1 + (step * 0.8) # 20% gap between plots
            lat2 = lat1 + (step * 0.8)
            
            f.write(f'''
    <Placemark>
      <name>Plot {i}-{j}</name>
      <ExtendedData>
        <Data name="Crop_Type"><value>{"Corn" if random.random() > 0.5 else "Wheat"}</value></Data>
        <Data name="Yield_Est"><value>{round(random.uniform(5.0, 15.0), 2)} tons</value></Data>
      </ExtendedData>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              {lon1},{lat1},0
              {lon2},{lat1},0
              {lon2},{lat2},0
              {lon1},{lat2},0
              {lon1},{lat1},0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>''')

    # Add a winding river
    f.write('''
    <Placemark>
      <name>Irrigation Canal</name>
      <ExtendedData>
        <Data name="Flow_Rate"><value>120 L/s</value></Data>
      </ExtendedData>
      <LineString>
        <coordinates>
          -122.105,37.395,0
          -122.095,37.410,0
          -122.080,37.415,0
          -122.065,37.425,0
          -122.050,37.445,0
        </coordinates>
      </LineString>
    </Placemark>''')

    f.write('  </Document>\n')
    f.write('</kml>\n')
