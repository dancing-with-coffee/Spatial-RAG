"use client";

import { useState } from "react";
import { useStore } from "../store/useStore";
import { QueryResponseSchema } from "../lib/schemas";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export default function QueryPanel() {
  const {
    query,
    setQuery,
    isLoading,
    setLoading,
    setError,
    handleQueryResponse,
    radiusM,
    setRadiusM,
    topK,
    setTopK,
    mapCenter,
    drawnRegion,
  } = useStore();

  const [includeAnswer, setIncludeAnswer] = useState(true);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          center_lat: mapCenter[0],
          center_lon: mapCenter[1],
          radius_m: radiusM,
          top_k: topK,
          region_geojson: drawnRegion,
          include_answer: includeAnswer,
        }),
      });

      if (!response.ok) {
        throw new Error(`Query failed: ${response.statusText}`);
      }

      const data = await response.json();
      const parsed = QueryResponseSchema.safeParse(data);

      if (!parsed.success) {
        console.error("Response validation error:", parsed.error);
        throw new Error("Invalid response from server");
      }

      handleQueryResponse(parsed.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-slate-800 p-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Query input */}
        <div>
          <label
            htmlFor="query"
            className="block text-sm font-medium text-slate-300 mb-1.5"
          >
            Spatial Query
          </label>
          <textarea
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., What are the zoning restrictions near Central Business District?"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg 
                       text-slate-100 placeholder-slate-500 
                       focus:outline-none focus:ring-2 focus:ring-spatial-500 focus:border-transparent
                       resize-none"
            rows={3}
          />
        </div>

        {/* Parameters */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Search Radius
            </label>
            <select
              value={radiusM}
              onChange={(e) => setRadiusM(Number(e.target.value))}
              className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded-md 
                         text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-spatial-500"
            >
              <option value={500}>500m</option>
              <option value={1000}>1km</option>
              <option value={2000}>2km</option>
              <option value={5000}>5km</option>
              <option value={10000}>10km</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">
              Results
            </label>
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded-md 
                         text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-spatial-500"
            >
              <option value={5}>5 docs</option>
              <option value={10}>10 docs</option>
              <option value={20}>20 docs</option>
              <option value={50}>50 docs</option>
            </select>
          </div>
        </div>

        {/* Include answer toggle */}
        <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={includeAnswer}
            onChange={(e) => setIncludeAnswer(e.target.checked)}
            className="w-4 h-4 rounded border-slate-600 bg-slate-800 
                       text-spatial-500 focus:ring-spatial-500 focus:ring-offset-slate-900"
          />
          Generate AI answer
        </label>

        {/* Submit button */}
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="w-full py-2.5 px-4 bg-spatial-600 hover:bg-spatial-500 
                     disabled:bg-slate-700 disabled:cursor-not-allowed
                     text-white font-medium rounded-lg
                     transition-colors duration-200
                     flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <svg
                className="animate-spin h-4 w-4"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Searching...
            </>
          ) : (
            <>
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              Search Spatial Documents
            </>
          )}
        </button>
      </form>
    </div>
  );
}

