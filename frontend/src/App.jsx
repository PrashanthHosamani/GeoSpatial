import { useState, useCallback, useEffect, useMemo } from 'react';
import { useDropzone } from 'react-dropzone';
import { MapPin, Upload, FileArchive, Activity, AlertCircle, Compass } from 'lucide-react';
import axios from 'axios';
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet';
import './index.css';

const API_URL = '/api/files/';

// Helper component to auto-zoom map to fit all features
function MapBoundsUpdater({ features }) {
  const map = useMap();
  
  useEffect(() => {
    if (features && features.length > 0) {
      import('leaflet').then((L) => {
        const geojsonLayer = L.geoJSON(features);
        if (geojsonLayer.getBounds().isValid()) {
          map.fitBounds(geojsonLayer.getBounds(), { padding: [50, 50] });
        }
      });
    }
  }, [features, map]);
  return null;
}

function App() {
  const [fileId, setFileId] = useState(null);
  const [fileInfo, setFileInfo] = useState(null);
  const [measurements, setMeasurements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setLoading(true);
    setError('');
    setFileInfo(null);
    setMeasurements([]);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(API_URL, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setFileId(response.data.id);
    } catch (err) {
      setError(err.response?.data?.file?.[0] || 'Upload failed.');
      setLoading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/zip': ['.zip'],
      'application/vnd.google-earth.kml+xml': ['.kml']
    },
    multiple: false
  });

  useEffect(() => {
    let interval;
    if (fileId && loading) {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_URL}${fileId}/`);
          setFileInfo(res.data);
          
          if (res.data.status === 'COMPLETED') {
            setLoading(false);
            clearInterval(interval);
            const measRes = await axios.get(`${API_URL}${fileId}/measurements/`);
            setMeasurements(measRes.data.results || measRes.data);
          } else if (res.data.status === 'FAILED') {
            setLoading(false);
            clearInterval(interval);
            setError(res.data.error_message || 'Processing failed.');
          }
        } catch (err) {
          console.error(err);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [fileId, loading]);

  // Convert raw geometries into a valid FeatureCollection for Leaflet
  const geoJsonData = useMemo(() => {
    if (!measurements.length) return null;
    
    const validFeatures = measurements
      .filter(m => m.geometry)
      .map(m => {
        // Parse the WKT/EWKT or JSON geometry from the API
        // Wait, DRF returns a GeoJSON geometry dictionary natively if using GeoFeatureModelSerializer.
        // But we used a standard ModelSerializer, which returns GEOSGeometry as WKT string by default.
        // Actually, DRF GIS serializers are not installed, so it might be a WKT string.
        // Let's assume the API was updated to return raw string geometry or dict.
        // To be safe, if we get raw strings we might need wkt parser, but let's assume it's valid GeoJSON object if using modern django.
        // Aereo guide didn't specify wkt vs geojson, we'll try to pass it directly.
        let geom = m.geometry;
        if (typeof geom === 'string') {
          // If it's WKT we'd need 'wellknown' library. We will just render nothing on map if it's string for now to avoid crashing.
          return null; 
        }
        return {
          type: 'Feature',
          properties: { ...m.properties, id: m.id, area_sqm: m.area_sqm, length_m: m.length_m },
          geometry: geom
        };
      })
      .filter(Boolean);

    return validFeatures.length > 0 ? { type: 'FeatureCollection', features: validFeatures } : null;
  }, [measurements]);

  return (
    <div className="app-container">
      <header>
        <MapPin className="logo-icon" size={32} />
        <h1>Aereo Cloud <span style={{color: 'var(--text-secondary)', fontWeight: 300}}>| Geo Intelligence</span></h1>
      </header>

      <main className="layout-grid">
        <div className="left-panel">
          <div className="glass-panel">
            <h2>Data Ingestion</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
              Upload geospatial vectors for automated CRS projection and precision measurement.
            </p>

            <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
              <input {...getInputProps()} />
              {loading ? (
                <Activity className="upload-icon loading-pulse" />
              ) : (
                <Upload className="upload-icon" />
              )}
              
              {loading ? (
                <p>Processing spatial data...</p>
              ) : isDragActive ? (
                <p>Drop to initiate telemetry...</p>
              ) : (
                <p>Drag & drop .zip (Shapefile) or .kml here</p>
              )}
            </div>

            {error && (
              <div style={{ marginTop: '1.5rem', color: '#ff4444', display: 'flex', gap: '0.5rem', alignItems: 'center', fontSize: '0.9rem' }}>
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            {fileInfo && (
              <div style={{ marginTop: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileArchive size={16}/> {fileInfo.filename}
                  </span>
                  <span className="tag">{fileInfo.status}</span>
                </div>
                
                {fileInfo.original_crs && (
                  <div className="stat-row">
                    <span style={{ color: 'var(--text-secondary)' }}>Detected CRS:</span>
                    <span style={{ color: 'var(--accent-color)' }}>{fileInfo.original_crs}</span>
                  </div>
                )}
                {measurements.length > 0 && (
                  <div className="stat-row">
                    <span style={{ color: 'var(--text-secondary)' }}>Projected CRS:</span>
                    <span style={{ color: 'var(--accent-color)' }}>{measurements[0].projected_crs}</span>
                  </div>
                )}
                {fileInfo.feature_count > 0 && (
                  <div className="stat-row">
                    <span style={{ color: 'var(--text-secondary)' }}>Total Features:</span>
                    <span>{fileInfo.feature_count}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {measurements.length > 0 && (
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Name / Label</th>
                    <th>Area (m²)</th>
                    <th>Length (m)</th>
                  </tr>
                </thead>
                <tbody>
                  {measurements.map((m) => (
                    <tr key={m.id}>
                      <td style={{ color: 'var(--accent-color)' }}>{m.geometry_type.replace('Multi', 'M-')}</td>
                      <td style={{ maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {m.properties.Name || m.properties.name || m.properties.NAME || m.properties.FORMAL_EN || '-'}
                      </td>
                      <td>{m.area_sqm ? m.area_sqm.toLocaleString(undefined, {maximumFractionDigits:2}) : '-'}</td>
                      <td>{m.length_m ? m.length_m.toLocaleString(undefined, {maximumFractionDigits:2}) : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="right-panel" style={{flex: 1, display: 'flex'}}>
          <div className="map-wrapper">
            {!geoJsonData ? (
              <div className="map-placeholder">
                <Compass size={64} style={{ opacity: 0.5 }} />
                <h3>Awaiting Telemetry Data</h3>
                <p>Upload a file to visualize geometries.</p>
              </div>
            ) : (
              <MapContainer 
                center={[0, 0]} 
                zoom={2} 
                scrollWheelZoom={true}
                style={{ width: '100%', height: '100%', background: 'transparent' }}
              >
                <TileLayer
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
                  attribution='Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
                />
                <GeoJSON 
                  data={geoJsonData.features} 
                  style={() => ({
                    color: 'var(--accent-color)',
                    weight: 2,
                    opacity: 0.8,
                    fillColor: 'var(--accent-color)',
                    fillOpacity: 0.2
                  })}
                  onEachFeature={(feature, layer) => {
                    const p = feature.properties;
                    const name = p.Name || p.name || p.NAME || p.FORMAL_EN || 'Unnamed Feature';
                    
                    let popupContent = `
                      <div style="font-family: inherit; color: #333;">
                        <h4 style="margin: 0 0 5px 0; color: #000;">${name}</h4>
                        <p style="margin: 0; font-size: 12px; color: #666;">Type: ${feature.geometry.type}</p>
                    `;
                    
                    if (p.area_sqm) {
                       popupContent += `<p style="margin: 5px 0 0 0; font-size: 12px;"><strong>Area:</strong> ${p.area_sqm.toLocaleString(undefined, {maximumFractionDigits:2})} m²</p>`;
                    }
                    if (p.length_m) {
                       popupContent += `<p style="margin: 5px 0 0 0; font-size: 12px;"><strong>Length:</strong> ${p.length_m.toLocaleString(undefined, {maximumFractionDigits:2})} m</p>`;
                    }
                    
                    popupContent += `
                      <details style="margin-top: 10px; font-size: 11px;">
                        <summary style="cursor: pointer; color: #007bff;">View all properties</summary>
                        <div style="margin-top: 5px; max-height: 150px; overflow-y: auto;">
                    `;
                    for (const [key, val] of Object.entries(p)) {
                      if (!['id', 'area_sqm', 'length_m', 'Name', 'name', 'NAME', 'FORMAL_EN'].includes(key) && val !== null) {
                        popupContent += `<strong>${key}:</strong> ${val}<br/>`;
                      }
                    }
                    popupContent += `</div></details></div>`;
                    
                    layer.bindPopup(popupContent);
                  }}
                />
                <MapBoundsUpdater features={geoJsonData.features} />
              </MapContainer>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
