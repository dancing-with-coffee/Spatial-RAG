import type { Geometry } from "./schemas";

/**
 * Normalize geometry to ensure it's valid GeoJSON.
 * Handles WKT strings, partial geometries, etc.
 */
export function normalizeGeometry(geom: any): Geometry | null {
  if (!geom) return null;

  // Already valid GeoJSON geometry
  if (geom.type && geom.coordinates) {
    return geom as Geometry;
  }

  // WKT POINT string
  if (typeof geom === "string" && geom.startsWith("POINT")) {
    const match = geom.match(/POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)/);
    if (match) {
      return {
        type: "Point",
        coordinates: [parseFloat(match[1]), parseFloat(match[2])],
      };
    }
  }

  // Object with lon/lat
  if (geom.lon !== undefined && geom.lat !== undefined) {
    return {
      type: "Point",
      coordinates: [geom.lon, geom.lat],
    };
  }

  // Object with x/y
  if (geom.x !== undefined && geom.y !== undefined) {
    return {
      type: "Point",
      coordinates: [geom.x, geom.y],
    };
  }

  return null;
}

/**
 * Get Leaflet-compatible [lat, lng] from GeoJSON Point geometry.
 */
export function getLatLngFromPoint(
  geometry: Geometry | null
): [number, number] | null {
  if (!geometry || geometry.type !== "Point") return null;
  const [lng, lat] = geometry.coordinates as [number, number];
  return [lat, lng];
}

/**
 * Get center point of any geometry.
 */
export function getGeometryCenter(
  geometry: Geometry | null
): [number, number] | null {
  if (!geometry) return null;

  switch (geometry.type) {
    case "Point": {
      const [lng, lat] = geometry.coordinates as [number, number];
      return [lat, lng];
    }
    case "Polygon": {
      // Simple centroid calculation
      const coords = geometry.coordinates[0] as [number, number][];
      const sumLng = coords.reduce((acc, c) => acc + c[0], 0);
      const sumLat = coords.reduce((acc, c) => acc + c[1], 0);
      return [sumLat / coords.length, sumLng / coords.length];
    }
    default:
      return null;
  }
}

/**
 * Convert geometry to GeoJSON Feature.
 */
export function toGeoJSONFeature(
  geometry: Geometry,
  properties: Record<string, any> = {}
) {
  return {
    type: "Feature" as const,
    geometry,
    properties,
  };
}

