import React from "react";

// Simple SVG illustrations for dress, heels, jacket, purse
export const WardrobeIllustrations: React.FC = () => (
  <div className="absolute inset-0 pointer-events-none z-0">
    {/* Top left purse */}
    <svg className="absolute top-10 left-10 w-16 h-16 opacity-80" viewBox="0 0 64 64" fill="none">
      <rect x="12" y="20" width="40" height="28" rx="6" fill="#E57373"/>
      <rect x="24" y="12" width="16" height="12" rx="8" fill="#E57373"/>
      <rect x="28" y="28" width="8" height="8" rx="2" fill="#F9A825"/>
    </svg>
    
    {/* Top right dress */}
    <svg className="absolute top-16 right-16 w-16 h-16 opacity-80" viewBox="0 0 64 64" fill="none">
      <rect x="20" y="28" width="24" height="24" rx="8" fill="#E57373"/>
      <rect x="26" y="14" width="12" height="18" rx="6" fill="#E57373"/>
    </svg>
    
    {/* Bottom left heels */}
    <svg className="absolute bottom-16 left-16 w-16 h-16 opacity-80" viewBox="0 0 64 64" fill="none">
      <path d="M12 52L42 22" stroke="#F9A825" strokeWidth="8" strokeLinecap="round"/>
      <rect x="34" y="44" width="12" height="8" rx="4" fill="#E57373"/>
    </svg>
    
    {/* Bottom right jacket */}
    <svg className="absolute bottom-16 right-16 w-16 h-16 opacity-80" viewBox="0 0 64 64" fill="none">
      <rect x="16" y="20" width="32" height="28" rx="6" fill="#B97455"/>
      <rect x="12" y="20" width="8" height="28" rx="2" fill="#B97455"/>
      <rect x="48" y="20" width="8" height="28" rx="2" fill="#B97455"/>
      <rect x="24" y="12" width="16" height="12" rx="8" fill="#B97455"/>
      <rect x="20" y="24" width="6" height="6" rx="1" fill="#D7CCC8"/>
      <rect x="38" y="24" width="6" height="6" rx="1" fill="#D7CCC8"/>
    </svg>
    
    {/* Center left dress */}
    <svg className="absolute top-1/2 left-10 -translate-y-1/2 w-16 h-16 opacity-80" viewBox="0 0 64 64" fill="none">
      <rect x="20" y="28" width="24" height="24" rx="8" fill="#E57373"/>
      <rect x="26" y="14" width="12" height="18" rx="6" fill="#E57373"/>
    </svg>
    
    {/* Center right shirt */}
    <svg className="absolute top-1/2 right-10 -translate-y-1/2 w-16 h-16 opacity-80" viewBox="0 0 64 64" fill="none">
      <rect x="16" y="20" width="32" height="28" rx="6" fill="#B97455"/>
      <rect x="24" y="12" width="16" height="12" rx="8" fill="#B97455"/>
    </svg>
  </div>
);
