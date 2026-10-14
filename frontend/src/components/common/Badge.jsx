import React from 'react';

const BADGE_VARIANTS = {
  // Statuses
  COMPLETED: 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60',
  CHECKED_IN: 'bg-blue-950/80 text-blue-400 border border-blue-800/60',
  SCHEDULED: 'bg-slate-800 text-slate-300 border border-slate-700',
  ASSIGNED: 'bg-indigo-950/80 text-indigo-400 border border-indigo-800/60',
  MISSED: 'bg-rose-950/80 text-rose-400 border border-rose-800/60',
  ACTIVE: 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60',
  INACTIVE: 'bg-slate-800 text-slate-400 border border-slate-700',
  SUSPENDED: 'bg-rose-950/80 text-rose-400 border border-rose-800/60',
  OPEN: 'bg-amber-950/80 text-amber-400 border border-amber-800/60',
  RESOLVED: 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60',

  // Severities
  LOW: 'bg-slate-800 text-slate-300 border border-slate-700',
  MEDIUM: 'bg-amber-950/80 text-amber-400 border border-amber-800/60',
  HIGH: 'bg-orange-950/80 text-orange-400 border border-orange-800/60',
  CRITICAL: 'bg-rose-950/80 text-rose-400 border border-rose-800/60 font-semibold',

  // Roles
  ADMIN: 'bg-purple-950/80 text-purple-300 border border-purple-800/60',
  SUPERVISOR: 'bg-cyan-950/80 text-cyan-300 border border-cyan-800/60',
  AUDITOR: 'bg-amber-950/80 text-amber-300 border border-amber-800/60',
  GUARD: 'bg-blue-950/80 text-blue-300 border border-blue-800/60',
};

export const Badge = ({ variant, label, className = '' }) => {
  const normalized = (variant || label || '').toUpperCase();
  const style = BADGE_VARIANTS[normalized] || 'bg-slate-800 text-slate-300 border border-slate-700';

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs tracking-wide transition-colors ${style} ${className}`}
    >
      {label || variant}
    </span>
  );
};
