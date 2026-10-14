import React, { useState, useEffect } from 'react';
import {
  Users,
  ShieldCheck,
  AlertTriangle,
  FileCheck2,
  MapPin,
  CalendarCheck,
  TrendingUp,
  Activity,
  Radio,
  Fingerprint
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';
import api from '../services/api';
import { Card } from '../components/common/Card';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';

export const AdminDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [recentAudits, setRecentAudits] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [analyticsData, auditsData] = await Promise.all([
        api.get('/dashboard/analytics'),
        api.get('/audit/logs?limit=6')
      ]);
      setAnalytics(analyticsData);
      setRecentAudits(auditsData || []);
    } catch (err) {
      console.error('Error loading dashboard', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading || !analytics) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">EXECUTIVE OPERATIONS & COMPLIANCE</h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time compliance validation, labor rules enforcement, and cryptographic audit monitoring.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchData}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors"
          >
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            Refresh Telemetry
          </button>
        </div>
      </div>

      {/* Top Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card
          title="Facility Compliance"
          value={`${analytics.overall_compliance_score}%`}
          subtitle="Aggregated Across All Sites"
          icon={ShieldCheck}
          color="emerald"
        />
        <Card
          title="Active Guards"
          value={analytics.total_guards}
          subtitle={`Across ${analytics.total_sites} Monitored Facilities`}
          icon={Users}
          color="blue"
        />
        <Card
          title="Open Exceptions"
          value={analytics.open_exceptions_count}
          subtitle={`${analytics.resolved_exceptions_count} Resolved (${analytics.exception_resolution_rate}%)`}
          icon={AlertTriangle}
          color={analytics.open_exceptions_count > 0 ? "amber" : "emerald"}
        />
        <Card
          title="Scheduled Shifts"
          value={analytics.total_assignments}
          subtitle="Enforced by Rules Engine"
          icon={CalendarCheck}
          color="purple"
        />
      </div>

      {/* Primary Analytics Section: Score & Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Compliance Gauge Card */}
        <div className="bg-slate-850/80 border border-slate-800 rounded-xl p-6 flex flex-col items-center justify-center text-center shadow-xl">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
            System Compliance Health
          </h3>
          <ScoreRing score={analytics.overall_compliance_score} size={150} strokeWidth={12} label="Integrity" />
          <div className="mt-6 w-full grid grid-cols-2 gap-2 text-left pt-4 border-t border-slate-800">
            <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase font-medium">Late Arrivals</span>
              <span className="text-sm font-bold text-amber-400">{analytics.late_arrivals_count}</span>
            </div>
            <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase font-medium">Missed Shifts</span>
              <span className="text-sm font-bold text-rose-400">{analytics.missed_shifts_count}</span>
            </div>
            <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase font-medium">GPS Breaches</span>
              <span className="text-sm font-bold text-rose-400">{analytics.gps_violations_count}</span>
            </div>
            <div className="p-2 bg-slate-900/60 rounded-lg border border-slate-800">
              <span className="text-[10px] text-slate-400 block uppercase font-medium">Overtime Incidents</span>
              <span className="text-sm font-bold text-amber-400">{analytics.overtime_count}</span>
            </div>
          </div>
        </div>

        {/* 7-Day Compliance Trend Chart */}
        <div className="lg:col-span-2 bg-slate-850/80 border border-slate-800 rounded-xl p-6 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-400" />
              7-Day Operational Compliance Trend
            </h3>
            <span className="text-xs text-slate-400 font-mono">Weighted Algorithm (0-100%)</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={analytics.compliance_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#cbd5e1' }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  name="Compliance %"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#10b981' }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Secondary Charts: Attendance & Audit Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Attendance Volume Chart */}
        <div className="bg-slate-850/80 border border-slate-800 rounded-xl p-6 shadow-xl">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
            <CalendarCheck className="w-4 h-4 text-purple-400" />
            Attendance Deployments & Completion
          </h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics.attendance_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                <Bar dataKey="scheduled" name="Scheduled" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="checked_in" name="Active / Completed" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="missed" name="Missed" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Tamper-Evident Audit Feed */}
        <div className="bg-slate-850/80 border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Fingerprint className="w-4 h-4 text-amber-400" />
              Recent Cryptographic Audit Events
            </h3>
            <span className="text-[10px] text-emerald-400 font-mono bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60">
              SHA-256 SECURED
            </span>
          </div>
          <div className="flex-1 space-y-2.5 overflow-y-auto">
            {recentAudits.map((a) => (
              <div
                key={a.id}
                className="p-3 bg-slate-900/70 border border-slate-800 rounded-lg text-xs flex items-center justify-between gap-3 hover:border-slate-700 transition-colors"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-200">{a.action}</span>
                    <Badge variant={a.entity_type} label={a.entity_type} />
                  </div>
                  <p className="text-slate-400 text-[11px] mt-0.5 font-mono">
                    By: {a.performed_by} • Hash: {a.record_hash.slice(0, 10)}...
                  </p>
                </div>
                <span className="text-slate-500 text-[10px] whitespace-nowrap">
                  {a.timestamp ? a.timestamp.slice(11, 19) : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
