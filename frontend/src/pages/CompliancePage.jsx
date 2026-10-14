import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  FileCheck,
  Building,
  Wrench,
  Clock,
  Filter
} from 'lucide-react';
import api from '../services/api';
import { ScoreRing } from '../components/common/ScoreRing';
import { Table } from '../components/common/Table';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { useAuth } from '../context/AuthContext';

export const CompliancePage = () => {
  const { isAdmin, isSupervisor } = useAuth();
  const [exceptions, setExceptions] = useState([]);
  const [sites, setSites] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  // Resolution modal
  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [activeException, setActiveException] = useState(null);
  const [resolutionNotes, setResolutionNotes] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (severityFilter) params.append('severity', severityFilter);

      const [excs, sRes, ana] = await Promise.all([
        api.get(`/audit/exceptions?${params.toString()}`),
        api.get('/sites'),
        api.get('/dashboard/analytics')
      ]);
      setExceptions(excs || []);
      setSites(sRes || []);
      setAnalytics(ana);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter, severityFilter]);

  const handleOpenResolve = (exc) => {
    setActiveException(exc);
    setResolutionNotes('');
    setResolveModalOpen(true);
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!activeException) return;
    try {
      await api.post(`/audit/exceptions/${activeException.id}/resolve`, {
        resolution_notes: resolutionNotes
      });
      setResolveModalOpen(false);
      fetchData();
    } catch (err) {
      alert(err?.message || 'Resolution failed');
    }
  };

  const columns = [
    {
      key: 'id',
      header: 'ID',
      render: (e) => <span className="font-mono text-xs text-slate-400">#{e.id}</span>
    },
    {
      key: 'violation_type',
      header: 'Violation Type',
      render: (e) => (
        <div>
          <span className="font-bold text-slate-100">{e.violation_type}</span>
          <span className="block text-[11px] text-slate-400">{e.site_name}</span>
        </div>
      )
    },
    {
      key: 'severity',
      header: 'Severity',
      render: (e) => <Badge variant={e.severity} label={e.severity} />
    },
    {
      key: 'status',
      header: 'Status',
      render: (e) => <Badge variant={e.status} label={e.status} />
    },
    {
      key: 'guard_name',
      header: 'Involved Officer',
      render: (e) => e.guard_name || '-'
    },
    {
      key: 'detected_at',
      header: 'Detected',
      render: (e) => (e.detected_at ? e.detected_at.slice(0, 16).replace('T', ' ') : '-')
    },
    {
      key: 'actions',
      header: 'Resolution',
      render: (e) => (
        e.status === 'OPEN' ? (
          (isAdmin || isSupervisor) && (
            <button
              onClick={() => handleOpenResolve(e)}
              className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-xs font-semibold shadow transition-colors"
            >
              Resolve
            </button>
          )
        ) : (
          <span className="text-[11px] text-slate-400 italic">
            Resolved: {e.resolved_by ? e.resolved_by.split('@')[0] : 'Admin'}
          </span>
        )
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">COMPLIANCE COMMAND CENTER</h2>
          <p className="text-xs text-slate-400 mt-1">
            Dynamic labor rule infraction tracking, geofence violations, and supervisor resolution workflows.
          </p>
        </div>
      </div>

      {/* Overview Cards: System Score + Facility Scores */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="bg-slate-850/80 border border-slate-800 rounded-xl p-5 flex flex-col items-center justify-center text-center shadow-xl">
          <ScoreRing score={analytics?.overall_compliance_score || 100} size={130} strokeWidth={10} label="Global Score" />
          <p className="text-xs text-slate-400 mt-3">Weighted Fleet Compliance</p>
        </div>

        <div className="lg:col-span-3 bg-slate-850/80 border border-slate-800 rounded-xl p-5 shadow-xl">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            Facility Compliance Breakdown
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {sites.map((s) => (
              <div key={s.id} className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg text-xs space-y-2">
                <div className="flex items-start justify-between">
                  <span className="font-bold text-slate-200 line-clamp-1">{s.name}</span>
                  <span className="font-bold text-emerald-400 font-mono">{s.compliance_score}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full rounded-full"
                    style={{ width: `${s.compliance_score}%` }}
                  />
                </div>
                <span className="text-[10px] text-slate-500 block truncate">{s.location_name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-850/60 p-3 rounded-xl border border-slate-800">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
        >
          <option value="">All Statuses</option>
          <option value="OPEN">OPEN Exceptions</option>
          <option value="RESOLVED">RESOLVED Exceptions</option>
        </select>

        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
        >
          <option value="">All Severities</option>
          <option value="CRITICAL">CRITICAL</option>
          <option value="HIGH">HIGH</option>
          <option value="MEDIUM">MEDIUM</option>
          <option value="LOW">LOW</option>
        </select>
      </div>

      <Table columns={columns} data={exceptions} loading={loading} searchPlaceholder="Search infractions..." />

      {/* Exception Resolution Modal */}
      <Modal
        isOpen={resolveModalOpen}
        onClose={() => setResolveModalOpen(false)}
        title="Resolve Compliance Exception"
      >
        <form onSubmit={handleResolveSubmit} className="space-y-4 text-xs">
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 space-y-1 text-slate-300">
            <p><b>Exception ID:</b> #{activeException?.id}</p>
            <p><b>Violation:</b> {activeException?.violation_type}</p>
            <p><b>Officer:</b> {activeException?.guard_name}</p>
            <p><b>Facility:</b> {activeException?.site_name}</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-300 uppercase mb-1">
              Resolution Investigation & Corrective Action Notes
            </label>
            <textarea
              required
              rows={4}
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Detail reasons, dispatch contacts, and corrective mitigation taken..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100 focus:border-blue-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setResolveModalOpen(false)}
              className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-semibold shadow-lg shadow-emerald-600/30"
            >
              Sign & Resolve
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
