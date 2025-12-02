"use client";

import { useEffect, useMemo } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  GeoJSON,
  useMap,
  Circle,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useStore } from "../store/useStore";
import { getGeometryCenter, normalizeGeometry } from "../lib/geojson";
import type { Document } from "../lib/schemas";

// Fix Leaflet default marker icon issue
const defaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const selectedIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [30, 49],
  iconAnchor: [15, 49],
  popupAnchor: [1, -40],
  shadowSize: [49, 49],
  className: "selected-marker",
});

L.Marker.prototype.options.icon = defaultIcon;

// Map center controller component
function MapController() {
  const map = useMap();
  const { documents, selectedDocumentId, mapCenter, mapZoom } = useStore();

  useEffect(() => {
    map.setView(mapCenter, mapZoom);
  }, [map, mapCenter, mapZoom]);

  // Fly to selected document
  useEffect(() => {
    if (selectedDocumentId) {
      const doc = documents.find((d) => d.id === selectedDocumentId);
      if (doc?.geometry) {
        const normalized = normalizeGeometry(doc.geometry);
        const center = getGeometryCenter(normalized);
        if (center) {
          map.flyTo(center, 15, { duration: 0.5 });
        }
      }
    }
  }, [map, selectedDocumentId, documents]);

  return null;
}

// Document marker component
function DocumentMarker({ doc }: { doc: Document }) {
  const { selectedDocumentId, setSelectedDocument } = useStore();
  const isSelected = selectedDocumentId === doc.id;

  const normalized = normalizeGeometry(doc.geometry);
  if (!normalized) return null;

  const center = getGeometryCenter(normalized);
  if (!center) return null;

  const hybridScore = doc.scores?.hybrid ?? 0;
  const semanticScore = doc.scores?.semantic ?? 0;
  const spatialScore = doc.scores?.spatial ?? 0;

  if (normalized.type === "Point") {
    return (
      <Marker
        position={center}
        icon={isSelected ? selectedIcon : defaultIcon}
        eventHandlers={{
          click: () => setSelectedDocument(doc.id),
        }}
      >
        <Popup>
          <div className="min-w-[200px]">
            <h3 className="font-semibold text-sm mb-1">{doc.title}</h3>
            <p className="text-xs text-gray-400 mb-2">
              {doc.content.slice(0, 100)}...
            </p>
            <div className="text-xs space-y-0.5">
              <div className="flex justify-between">
                <span>Hybrid:</span>
                <span className="font-mono">{hybridScore.toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span>Semantic:</span>
                <span className="font-mono">{semanticScore.toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span>Spatial:</span>
                <span className="font-mono">{spatialScore.toFixed(3)}</span>
              </div>
              {doc.spatial_distance_m && (
                <div className="flex justify-between">
                  <span>Distance:</span>
                  <span className="font-mono">
                    {doc.spatial_distance_m.toFixed(0)}m
                  </span>
                </div>
              )}
            </div>
          </div>
        </Popup>
      </Marker>
    );
  }

  // Render polygons
  return (
    <GeoJSON
      data={{
        type: "Feature",
        geometry: normalized,
        properties: { id: doc.id },
      }}
      style={{
        color: isSelected ? "#22c55e" : "#0ea5e9",
        weight: isSelected ? 3 : 2,
        fillOpacity: isSelected ? 0.3 : 0.2,
      }}
      eventHandlers={{
        click: () => setSelectedDocument(doc.id),
      }}
    >
      <Popup>
        <div className="min-w-[200px]">
          <h3 className="font-semibold text-sm mb-1">{doc.title}</h3>
          <p className="text-xs text-gray-400">{doc.content.slice(0, 100)}...</p>
        </div>
      </Popup>
    </GeoJSON>
  );
}

export default function Map() {
  const { documents, mapCenter, mapZoom, drawnRegion, radiusM } = useStore();

  // Dark map tiles
  const tileUrl = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
  const attribution =
    '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>';

  return (
    <MapContainer
      center={mapCenter}
      zoom={mapZoom}
      className="h-full w-full rounded-lg"
      style={{ background: "#1e293b" }}
    >
      <TileLayer url={tileUrl} attribution={attribution} />
      <MapController />

      {/* Search radius circle */}
      {!drawnRegion && (
        <Circle
          center={mapCenter}
          radius={radiusM}
          pathOptions={{
            color: "#22c55e",
            fillColor: "#22c55e",
            fillOpacity: 0.1,
            weight: 1,
            dashArray: "5, 5",
          }}
        />
      )}

      {/* Document markers */}
      {documents.map((doc) => (
        <DocumentMarker key={doc.id} doc={doc} />
      ))}
    </MapContainer>
  );
}

