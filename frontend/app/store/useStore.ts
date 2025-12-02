import { create } from "zustand";
import type { Document, QueryResponse } from "../lib/schemas";

interface SpatialRAGState {
  // Query state
  query: string;
  isLoading: boolean;
  error: string | null;

  // Results state
  answer: string | null;
  documents: Document[];
  selectedDocumentId: string | null;

  // Map state
  mapCenter: [number, number];
  mapZoom: number;
  drawnRegion: any | null;

  // Search parameters
  radiusM: number;
  topK: number;

  // Actions
  setQuery: (query: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setAnswer: (answer: string | null) => void;
  setDocuments: (documents: Document[]) => void;
  setSelectedDocument: (id: string | null) => void;
  setMapCenter: (center: [number, number]) => void;
  setMapZoom: (zoom: number) => void;
  setDrawnRegion: (region: any | null) => void;
  setRadiusM: (radius: number) => void;
  setTopK: (topK: number) => void;

  // Composite actions
  handleQueryResponse: (response: QueryResponse) => void;
  reset: () => void;
}

const DEFAULT_CENTER: [number, number] = [31.5204, 74.3587]; // Lahore
const DEFAULT_ZOOM = 12;

export const useStore = create<SpatialRAGState>((set) => ({
  // Initial state
  query: "",
  isLoading: false,
  error: null,
  answer: null,
  documents: [],
  selectedDocumentId: null,
  mapCenter: DEFAULT_CENTER,
  mapZoom: DEFAULT_ZOOM,
  drawnRegion: null,
  radiusM: 1000,
  topK: 10,

  // Actions
  setQuery: (query) => set({ query }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  setAnswer: (answer) => set({ answer }),
  setDocuments: (documents) => set({ documents }),
  setSelectedDocument: (selectedDocumentId) => set({ selectedDocumentId }),
  setMapCenter: (mapCenter) => set({ mapCenter }),
  setMapZoom: (mapZoom) => set({ mapZoom }),
  setDrawnRegion: (drawnRegion) => set({ drawnRegion }),
  setRadiusM: (radiusM) => set({ radiusM }),
  setTopK: (topK) => set({ topK }),

  // Handle query response
  handleQueryResponse: (response) =>
    set({
      answer: response.answer,
      documents: response.documents,
      error: null,
    }),

  // Reset to initial state
  reset: () =>
    set({
      query: "",
      isLoading: false,
      error: null,
      answer: null,
      documents: [],
      selectedDocumentId: null,
      drawnRegion: null,
    }),
}));

