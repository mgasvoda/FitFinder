import { Search } from 'lucide-react';
import React from "react";

export const FitFinderHeader: React.FC = () => (
  <header className="flex items-center justify-between py-4 px-2">
    <div className="flex items-center">
      <div className="mr-3 text-3xl">
        <svg className="w-10 h-10" viewBox="0 0 64 64" fill="none">
          <rect x="12" y="20" width="40" height="28" rx="6" fill="#E57373"/>
          <rect x="24" y="12" width="16" height="12" rx="8" fill="#E57373"/>
          <rect x="28" y="28" width="8" height="8" rx="2" fill="#F9A825"/>
        </svg>
      </div>
      <h1 className="text-4xl font-bold tracking-tight text-purple-900 font-serif">
        FitFinder
      </h1>
    </div>
    <Search className="w-7 h-7 text-purple-900" aria-label="Search" />
  </header>
);
