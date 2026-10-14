import React, { useState, useEffect } from 'react';
import {
  MapPin,
  Users,
  ShieldCheck,
  AlertCircle,
  Clock,
  CheckCircle,
  XCircle,
  FileText,
  Radio,
  Wrench
} from 'lucide-react';
import api from '../services/api';
import { Card } from '../components/common/Card';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { useWebSocket } from '../hooks/useWebSocket';

export const SupervisorDashboard = () => {
  const [sites, setSites] = useState([]);
  const [selectedSiteId, setSelectedSiteId] = useState('');
  const [siteDashboard, setSiteDashboard] = useState(null);
  const [exceptions, setExceptions] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [resolveModalOpen, setResolveModalOpen] = useState(false);
  const [currentException, setCurrentException] = useState(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [loading, setLoading] = useState(true);

  // Load sites
  const fetchSites = async () => {
    try {
      const res = await api.get('/sites');
      setSites(res || []);
      if (res && res.length > 0 && !selectedSiteId) {
        setSelectedSiteId(String(res[0].id));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSiteMetrics = async (siteId) => {
    if (!siteId) return;
    try {
      setLoading(true);
      const [metrics, excs, asgs] = await Promise.all([
        api.get(`/dashboard/site/${siteId}`),
        api.get(`/audit/exceptions?site=${siteId}&status=OPEN`),
        api.get(`/assignments?site_id=${siteId}&date=${new Date().toISOString().slice(0, 10)}`)
      ]);
      setSiteDashboard(metrics);
      setExceptions(excs || []);
      setAssignments(asgs || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSites();
  }, []);

  useEffect(() => {
    if (selectedSiteId) {
      fetchSiteMetrics(selectedSiteId);
    }
  }, [selectedSiteId]);

  // Real-time updates via WebSocket!
  useWebSocket('/ws/compliance', (event) => {
    if (event.event === 'check_in' || event.event === 'check_out' || event.event === 'notification') {
      if (selectedSiteId) {
        fetchSiteMetrics(selectedSiteId);
      }
    }
  });

  const handleOpenResolve = (exc) => {
    setCurrentException(exc);
    setResolutionNotes('');
    setResolveModalOpen(true);
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!currentException) return;
    try {
      await api.post(`/audit/exceptions/${currentException.id}/resolve`, {
        resolution_notes: resolutionNotes
      });
      setResolveModalOpen(false);
      fetchSiteMetrics(selectedSiteId);
    } catch (err) {
      alert(err?.message || 'Failed to resolve exception');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Site Picker */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">SUPERVISOR DISPATCH & COMPLIANCE</h2>
          <p className="text-xs text-slate-400 mt-1">
            Active guard tracking, geofence status, and immediate operational exception resolution.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400 font-semibold uppercase">Active Facility:</label>
          <select
            value={selectedSiteId}
            onChange={(e) => setSelectedSiteId(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-1.5 text-xs font-semibold focus:outline-none focus:border-blue-500"
          >
            {sites.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading || !siteDashboard ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <>
          {/* Metrics Overview Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card
              title="Today's Guards"
              value={siteDashboard.total_guards}
              subtitle={`${siteDashboard.checked_in_guards} On-Duty • ${siteDashboard.completed_guards} Completed`}
              icon={Users}
              color="blue"
            />
            <Card
              title="Site Compliance"
              value={`${siteDashboard.compliance_score}%`}
              subtitle={siteDashboard.site_name}
              icon={ShieldCheck}
              color="emerald"
            />
            <Card
              title="Late Check-ins"
              value={siteDashboard.late_guards}
              subtitle="Lapsed Grace Period"
              icon={Clock}
              color="amber"
            />
            <Card
              title="Missing Guards"
              value={siteDashboard.missing_guards}
              subtitle="Shift Not Reported"
              icon={XCircle}
              color={siteDashboard.missing_guards > 0 ? "rose" : "slate"}
            />
          </div>

          {/* Operational Status & Open Exceptions */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Today's Guard Deployment Roster */}
            <div className="lg:col-span-2 bg-slate-850/80 border border-slate-800 rounded-xl p-5 shadow-xl">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center justify-between">
                <span>Guard Roster (Today)</span>
                <span className="text-xs text-blue-400 font-mono">{assignments.length} Officers Scheduled</span>
              </h3>
              <div className="space-y-2.5 overflow-x-auto">
                {assignments.length === 0 ? (
                  <p className="text-xs text-slate-500 py-8 text-center">No assignments scheduled for today at this site.</p>
                ) : (
                  assignments.map((asg) => (
                    <div
                      key={asg.id}
                      className="p-3 bg-slate-900/70 border border-slate-800 rounded-lg flex items-center justify-between gap-3 text-xs"
                    >
                      <div>
                        <span className="font-bold text-slate-200">{asg.user_name}</span>
                        <p className="text-slate-400 text-[11px] mt-0.5">
                          {asg.shift_name} ({asg.shift_start} - {asg.shift_end})
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {asg.compliance_violations && asg.compliance_violations.length > 0 && (
                          <span className="text-[10px] text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800/60 font-semibold">
                            ⚠️ {asg.compliance_violations.length} Flags
                          </span>
                        )}
                        <Badge variant={asg.status} label={asg.status} />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Open Compliance Exceptions at Site */}
            <div className="bg-slate-850/80 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center justify-between">
                <span>Open Exceptions</span>
                <span className="text-xs text-rose-400 font-bold">{exceptions.length} Active</span>
              </h3>
              <div className="flex-1 space-y-3 overflow-y-auto max-h-96">
                {exceptions.length === 0 ? (
                  <div className="text-center py-12 text-slate-500 text-xs">
                    <CheckCircle className="w-8 h-8 mx-auto text-emerald-500 mb-2" />
                    All exceptions resolved. Site is fully compliant.
                  </div>
                ) : (
                  exceptions.map((exc) => (
                    <div
                      key={exc.id}
                      className="p-3 bg-rose-950/20 border border-rose-900/50 rounded-lg text-xs space-y-2"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <Badge variant={exc.severity} label={exc.severity} />
                          <span className="font-bold text-rose-300 ml-2">{exc.violation_type}</span>
                        </div>
                        <button
                          onClick={() => handleOpenResolve(exc)}
                          className="px-2 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-[11px] font-semibold transition-colors"
                        >
                          Resolve
                        </button>
                      </div>
                      <p className="text-slate-300 text-[11px]">{exc.resolution_notes || 'Operational breach detected.'}</p>
                      <p className="text-slate-500 text-[10px]">
                        Officer: {exc.guard_name || 'N/A'} • Shift: {exc.shift_name || 'N/A'}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Resolution Modal */}
      <Modal
        isOpen={resolveModalOpen}
        onClose={() => setResolveModalOpen(false)}
        title="Resolve Compliance Exception"
      >
        <form onSubmit={handleResolveSubmit} className="space-y-4">
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-300 space-y-1">
            <p><b>Violation:</b> {currentException?.violation_type}</p>
            <p><b>Officer:</b> {currentException?.guard_name}</p>
            <p><b>Detected At:</b> {currentException?.detected_at}</p>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase">
              Supervisor Resolution Notes (Auditable)
            </label>
            <textarea
              required
              rows={4}
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Detail investigation findings, corrective actions taken, and authorization rationale..."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setResolveModalOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-emerald-600/30"
            >
              Sign & Resolve Exception
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
