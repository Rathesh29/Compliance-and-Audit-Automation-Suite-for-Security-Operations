import React from 'react';

export const ScoreRing = ({ score = 100, size = 120, strokeWidth = 10, label = "Score" }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, Number(score) || 0));
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  let colorClass = 'text-emerald-500';
  let statusText = 'EXCELLENT';
  let glowColor = 'rgba(16, 185, 129, 0.2)';

  if (clampedScore < 60) {
    colorClass = 'text-rose-500';
    statusText = 'CRITICAL';
    glowColor = 'rgba(239, 68, 68, 0.2)';
  } else if (clampedScore < 75) {
    colorClass = 'text-amber-500';
    statusText = 'WARNING';
    glowColor = 'rgba(245, 158, 11, 0.2)';
  } else if (clampedScore < 90) {
    colorClass = 'text-blue-500';
    statusText = 'GOOD';
    glowColor = 'rgba(59, 130, 246, 0.2)';
  }

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="w-full h-full transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            className="text-slate-800"
            strokeWidth={strokeWidth}
            stroke="currentColor"
            fill="transparent"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            className={`${colorClass} transition-all duration-1000 ease-out`}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            stroke="currentColor"
            fill="transparent"
            style={{ filter: `drop-shadow(0 0 6px ${glowColor})` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-black text-slate-100 tracking-tight">{clampedScore.toFixed(0)}%</span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 mt-0.5">{label}</span>
        </div>
      </div>
      <div className="mt-2 text-center">
        <span className={`text-xs font-bold tracking-wider px-2 py-0.5 rounded-full border ${
          statusText === 'EXCELLENT' ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60' :
          statusText === 'GOOD' ? 'bg-blue-950/60 text-blue-400 border-blue-800/60' :
          statusText === 'WARNING' ? 'bg-amber-950/60 text-amber-400 border-amber-800/60' :
          'bg-rose-950/60 text-rose-400 border-rose-800/60'
        }`}>
          {statusText}
        </span>
      </div>
    </div>
  );
};
