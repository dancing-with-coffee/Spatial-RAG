"use client";

import { useStore } from "../store/useStore";

export default function AnswerDisplay() {
  const { answer, isLoading, query } = useStore();

  if (!answer && !isLoading) {
    return null;
  }

  return (
    <div className="bg-slate-900/80 backdrop-blur-sm rounded-xl border border-slate-800 p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-spatial-500 to-spatial-600 flex items-center justify-center">
          <svg
            className="w-3.5 h-3.5 text-white"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        </div>
        <h3 className="text-sm font-medium text-slate-200">AI Answer</h3>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <div className="h-3 bg-slate-700 rounded animate-pulse w-full" />
          <div className="h-3 bg-slate-700 rounded animate-pulse w-5/6" />
          <div className="h-3 bg-slate-700 rounded animate-pulse w-4/6" />
        </div>
      ) : (
        <div className="prose prose-sm prose-invert max-w-none">
          <div className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
            {answer}
          </div>
        </div>
      )}

      {query && !isLoading && (
        <div className="mt-3 pt-3 border-t border-slate-800">
          <p className="text-[10px] text-slate-500">
            Query: &quot;{query}&quot;
          </p>
        </div>
      )}
    </div>
  );
}

