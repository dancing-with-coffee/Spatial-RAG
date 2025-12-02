"use client";

import { useStore } from "../store/useStore";
import type { Document } from "../lib/schemas";

function DocumentCard({ doc, index }: { doc: Document; index: number }) {
  const { selectedDocumentId, setSelectedDocument } = useStore();
  const isSelected = selectedDocumentId === doc.id;

  const hybridScore = doc.scores?.hybrid ?? 0;
  const semanticScore = doc.scores?.semantic ?? 0;
  const spatialScore = doc.scores?.spatial ?? 0;
  const docType = doc.metadata?.doc_type || "document";

  return (
    <div
      onClick={() => setSelectedDocument(isSelected ? null : doc.id)}
      className={`
        p-3 rounded-lg border cursor-pointer transition-all duration-200
        ${
          isSelected
            ? "bg-spatial-900/30 border-spatial-500 ring-1 ring-spatial-500/50"
            : "bg-slate-800/50 border-slate-700 hover:border-slate-600 hover:bg-slate-800"
        }
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-700 text-xs font-medium flex items-center justify-center">
            {index + 1}
          </span>
          <h3 className="text-sm font-medium text-slate-200 line-clamp-1">
            {doc.title}
          </h3>
        </div>
        <span
          className={`
            flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium uppercase
            ${
              docType === "zoning"
                ? "bg-purple-900/50 text-purple-300"
                : docType === "permit"
                ? "bg-blue-900/50 text-blue-300"
                : docType === "traffic"
                ? "bg-amber-900/50 text-amber-300"
                : docType === "environmental"
                ? "bg-emerald-900/50 text-emerald-300"
                : "bg-slate-700 text-slate-400"
            }
          `}
        >
          {docType}
        </span>
      </div>

      {/* Content preview */}
      <p className="text-xs text-slate-400 line-clamp-2 mb-2">{doc.content}</p>

      {/* Scores */}
      <div className="flex items-center gap-3 text-[10px] text-slate-500">
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-spatial-500" />
          <span>H: {hybridScore.toFixed(2)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-blue-500" />
          <span>S: {semanticScore.toFixed(2)}</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          <span>G: {spatialScore.toFixed(2)}</span>
        </div>
        {doc.spatial_distance_m && (
          <div className="ml-auto text-slate-500">
            {doc.spatial_distance_m < 1000
              ? `${doc.spatial_distance_m.toFixed(0)}m`
              : `${(doc.spatial_distance_m / 1000).toFixed(1)}km`}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ResultsList() {
  const { documents, isLoading, error } = useStore();

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-800 rounded-lg p-4 text-center">
        <p className="text-red-400 text-sm">{error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="p-3 rounded-lg bg-slate-800/50 border border-slate-700 animate-pulse"
          >
            <div className="h-4 bg-slate-700 rounded w-3/4 mb-2" />
            <div className="h-3 bg-slate-700 rounded w-full mb-1" />
            <div className="h-3 bg-slate-700 rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        <svg
          className="w-12 h-12 mx-auto mb-3 opacity-50"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
          />
        </svg>
        <p className="text-sm">No results yet</p>
        <p className="text-xs mt-1">Enter a query to search spatial documents</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-400 mb-2 px-1">
        <span>{documents.length} documents found</span>
        <span>Sorted by hybrid score</span>
      </div>
      <div className="space-y-2 max-h-[calc(100vh-400px)] overflow-y-auto pr-1">
        {documents.map((doc, index) => (
          <DocumentCard key={doc.id} doc={doc} index={index} />
        ))}
      </div>
    </div>
  );
}

