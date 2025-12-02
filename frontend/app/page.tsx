"use client";

import dynamic from "next/dynamic";
import QueryPanel from "./components/QueryPanel";
import ResultsList from "./components/ResultsList";
import AnswerDisplay from "./components/AnswerDisplay";

// Dynamic import for Map to avoid SSR issues with Leaflet
const Map = dynamic(() => import("./components/Map"), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full bg-slate-800 rounded-lg animate-pulse flex items-center justify-center">
      <span className="text-slate-500">Loading map...</span>
    </div>
  ),
});

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-[1920px] mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-spatial-500 to-spatial-600 flex items-center justify-center">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">Spatial-RAG</h1>
              <p className="text-[10px] text-slate-500 -mt-0.5">
                Geospatial Retrieval Augmented Generation
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400">
              <span className="w-2 h-2 rounded-full bg-spatial-500 animate-pulse" />
              <span>Connected</span>
            </div>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <svg
                className="w-5 h-5 text-slate-400"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
              </svg>
            </a>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-[1920px] mx-auto p-4 grid grid-cols-1 lg:grid-cols-3 gap-4 h-[calc(100vh-60px)]">
        {/* Left panel - Query and Results */}
        <div className="lg:col-span-1 flex flex-col gap-4 overflow-hidden">
          <QueryPanel />
          <AnswerDisplay />
          <div className="flex-1 overflow-hidden">
            <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-slate-800 p-4 h-full overflow-hidden">
              <h2 className="text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
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
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                Retrieved Documents
              </h2>
              <ResultsList />
            </div>
          </div>
        </div>

        {/* Right panel - Map */}
        <div className="lg:col-span-2 bg-slate-900/80 backdrop-blur-sm rounded-xl border border-slate-800 p-2 overflow-hidden">
          <Map />
        </div>
      </div>

      {/* Footer attribution */}
      <div className="fixed bottom-2 right-2 text-[10px] text-slate-600">
        Spatial-RAG • Hybrid Retrieval Engine
      </div>
    </main>
  );
}

