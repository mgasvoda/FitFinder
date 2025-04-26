import React from "react";

export const BackgroundConfetti: React.FC = () => (
  <div className="absolute inset-0 -z-10 pointer-events-none bg-pink-200">
    {/* Confetti dots and squiggles using Tailwind utility classes */}
    <div className="w-full h-full">
      {/* Use multiple absolutely positioned spans for confetti */}
      {Array.from({ length: 40 }).map((_, i) => (
        <span
          key={i}
          className={`absolute opacity-60`}
          style={{
            background: i % 5 === 0 ? "#FFC107" : "#FF8A65",
            width: `${8 + (i % 3) * 4}px`,
            height: `${8 + (i % 2) * 4}px`,
            borderRadius: i % 2 === 0 ? '50%' : '0',
            top: `${Math.random() * 95}%`,
            left: `${Math.random() * 95}%`,
          }}
        />
      ))}
      
      {/* Add some squiggly lines */}
      {Array.from({ length: 15 }).map((_, i) => (
        <div
          key={`line-${i}`}
          className="absolute opacity-30"
          style={{
            width: `${50 + Math.random() * 100}px`,
            height: '3px',
            background: '#FF8A65',
            top: `${Math.random() * 95}%`,
            left: `${Math.random() * 95}%`,
            transform: `rotate(${Math.random() * 360}deg)`,
            borderRadius: '50%',
          }}
        />
      ))}
    </div>
  </div>
);
