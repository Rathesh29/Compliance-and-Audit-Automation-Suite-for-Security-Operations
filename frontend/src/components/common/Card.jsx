import React from 'react';

export const Card = ({ title, value, subtitle, icon: Icon, color = 'blue', trend, className = '' }) => {
  const colorMap = {
    blue: 'text-blue-400 bg-blue-950/40 border-blue-800/40',
    emerald: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/40',
    amber: 'text-amber-400 bg-amber-950/40 border-amber-800/40',
    rose: 'text-rose-400 bg-rose-950/40 border-rose-800/40',
    purple: 'text-purple-400 bg-purple-950/40 border-purple-800/40',
    cyan: 'text-cyan-400 bg-cyan-950/40 border-cyan-800/40',
  };

  const activeColor = colorMap[color] || colorMap.blue;

  return (
    <div className={`bg-slate-850/90 border border-slate-800 rounded-xl p-5 shadow-lg backdrop-blur-sm transition-all hover:border-slate-700 ${className}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400">{title}</p>
          <h3 className="text-2xl font-bold mt-1 text-slate-100">{value}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
          {trend && (
            <div className="mt-2 flex items-center text-xs">
              <span className={trend > 0 ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
                {trend > 0 ? `+${trend}%` : `${trend}%`}
              </span>
              <span className="text-slate-500 ml-1.5">vs previous cycle</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className={`p-3 rounded-lg border ${activeColor}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
    </div>
  );
};
