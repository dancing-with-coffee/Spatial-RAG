import { z } from "zod";

// Geometry schema for GeoJSON
export const GeometrySchema = z.object({
  type: z.enum([
    "Point",
    "Polygon",
    "MultiPolygon",
    "LineString",
    "MultiLineString",
  ]),
  coordinates: z.any(),
});

// Scores schema
export const ScoresSchema = z.object({
  semantic: z.number().nullable().optional(),
  spatial: z.number().nullable().optional(),
  hybrid: z.number().nullable().optional(),
});

// Document schema
export const DocumentSchema = z.object({
  id: z.string(),
  title: z.string(),
  content: z.string(),
  geometry: GeometrySchema.nullable().optional(),
  metadata: z.record(z.any()).nullable().optional(),
  scores: ScoresSchema.nullable().optional(),
  spatial_distance_m: z.number().nullable().optional(),
});

// Query response schema
export const QueryResponseSchema = z.object({
  query: z.string(),
  answer: z.string().nullable().optional(),
  documents: z.array(DocumentSchema),
  total_count: z.number(),
});

// Query request schema
export const QueryRequestSchema = z.object({
  query: z.string().min(1, "Query is required"),
  region_geojson: z.any().nullable().optional(),
  center_lon: z.number().nullable().optional(),
  center_lat: z.number().nullable().optional(),
  radius_m: z.number().nullable().optional(),
  top_k: z.number().nullable().optional(),
  include_answer: z.boolean().optional().default(true),
});

// Types derived from schemas
export type Geometry = z.infer<typeof GeometrySchema>;
export type Scores = z.infer<typeof ScoresSchema>;
export type Document = z.infer<typeof DocumentSchema>;
export type QueryResponse = z.infer<typeof QueryResponseSchema>;
export type QueryRequest = z.infer<typeof QueryRequestSchema>;

