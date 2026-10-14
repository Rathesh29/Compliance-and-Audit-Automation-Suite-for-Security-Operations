import React, { useState, useEffect } from 'react';
import { CalendarCheck, Plus, AlertTriangle, ShieldCheck, Check, Filter } from 'lucide-react';
import api from '../services/api';
import { Table } from '../components/common/Table';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { useAuth } from '../context/AuthContext';

export const AssignmentsPage = () => {
  const { isAdmin, isSupervisor } = useAuth();
  const [assignments, setAssignments] = useState([]);
  const [guards, setGuards] = useState([]);
  const [sites, setSites] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [siteFilter, setSiteFilter] = useState('');
  const [guardFilter, setGuardFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');

  // Modal & Form State
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    user_id: '',
    site_id: '',
    shift_id: '',
    date: new Date().toISOString().slice(0, 10),
    override_violations: false,
    override_reason: ''
  });

  // Pre-check compliance feedback
  const [preCheckResult, setPreCheckResult] = useState(null);
  const [preChecking, setPreChecking] = useState(false);

  const fetchDependencies = async () => {
    try {
      const [gRes, sRes, shRes] = await Promise.all([
        api.get('/users?role=GUARD'),
        api.get('/sites'),
        api.get('/shifts')
      ]);
      setGuards(gRes || []);
      setSites(sRes || []);
      setShifts(shRes || []);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchAssignments = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (siteFilter) params.append('site_id', siteFilter);
      if (guardFilter) params.append('user_id', guardFilter);
      if (statusFilter) params.append('status', statusFilter);
      if (dateFilter) params.append('date', dateFilter);

      const res = await api.get(`/assignments?${params.toString()}`);
      setAssignments(res || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDependencies();
  }, []);

  useEffect(() => {
    fetchAssignments();
  }, [siteFilter, guardFilter, statusFilter, dateFilter]);

  // Live pre-submission compliance check!
  const runPreCheck = async () => {
    if (!formData.user_id || !formData.site_id || !formData.shift_id || !formData.date) {
      return;
    }
    setPreChecking(true);
    try {
      const res = await api.post('/assignments/validate', {
        user_id: parseInt(formData.user_id),
        site_id: parseInt(formData.site_id),
        shift_id: parseInt(formData.shift_id),
        date: formData.date
      });
      setPreCheckResult(res);
    } catch (e) {
      console.error(e);
    } finally {
      setPreChecking(false);
    }
  };

  useEffect(() => {
    if (modalOpen) {
      runPreCheck();
    }
  }, [formData.user_id, formData.site_id, formData.shift_id, formData.date, modalOpen]);

  const handleOpenCreate = () => {
    setFormData({
      user_id: guards[0]?.id ? String(guards[0].id) : '',
      site_id: sites[0]?.id ? String(sites[0].id) : '',
      shift_id: shifts[0]?.id ? String(shifts[0].id) : '',
      date: new Date().toISOString().slice(0, 10),
      override_violations: false,
      override_reason: ''
    });
    setPreCheckResult(null);
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/assignments', {
        user_id: parseInt(formData.user_id),
        site_id: parseInt(formData.site_id),
        shift_id: parseInt(formData.shift_id),
        date: formData.date,
        override_violations: formData.override_violations,
        override_reason: formData.override_reason
      });
      setModalOpen(false);
      fetchAssignments();
    } catch (err) {
      alert(err?.message || 'Assignment creation rejected by compliance rules');
    }
  };

  const columns = [
    {
      key: 'user_name',
      header: 'Assigned Guard',
      render: (a) => (
        <div>
          <span className="font-bold text-slate-100">{a.user_name}</span>
          <span className="block text-slate-400 text-xs">{a.user_email}</span>
        </div>
      )
    },
    {
      key: 'site_name',
      header: 'Site Facility',
      render: (a) => a.site_name
    },
    {
      key: 'shift_name',
      header: 'Shift & Hours',
      render: (a) => (
        <div>
          <span className="font-medium text-slate-200">{a.shift_name}</span>
          <span className="block font-mono text-[11px] text-slate-400">
            {a.shift_start} - {a.shift_end}
          </span>
        </div>
      )
    },
    {
      key: 'date',
      header: 'Shift Date',
      render: (a) => <span className="font-mono text-xs">{a.date}</span>
    },
    {
      key: 'status',
      header: 'Lifecycle Status',
      render: (a) => <Badge variant={a.status} label={a.status} />
    },
    {
      key: 'compliance',
      header: 'Compliance State',
      render: (a) => (
        a.compliance_violations && a.compliance_violations.length > 0 ? (
          <span className="text-[11px] text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800 font-semibold">
            ⚠️ {a.compliance_violations.length} Flags
          </span>
        ) : (
          <span className="text-[11px] text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800 font-semibold">
            ✓ Compliant
          </span>
        )
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">GUARD ASSIGNMENTS & ROSTERING</h2>
          <p className="text-xs text-slate-400 mt-1">
            Pre-flight labor rule validation (daily/weekly hours, rest gaps) and administrative override controls.
          </p>
        </div>
        {(isAdmin || isSupervisor) && (
          <button
            onClick={handleOpenCreate}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-lg shadow-blue-600/20 self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Create Assignment</span>
          </button>
        )}
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-850/60 p-3 rounded-xl border border-slate-800">
        <select
          value={siteFilter}
          onChange={(e) => setSiteFilter(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
        >
          <option value="">All Sites</option>
          {sites.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        <select
          value={guardFilter}
          onChange={(e) => setGuardFilter(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
        >
          <option value="">All Officers</option>
          {guards.map((g) => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
        >
          <option value="">All Statuses</option>
          <option value="SCHEDULED">SCHEDULED</option>
          <option value="CHECKED_IN">CHECKED_IN</option>
          <option value="COMPLETED">COMPLETED</option>
          <option value="MISSED">MISSED</option>
        </select>

        <input
          type="date"
          value={dateFilter}
          onChange={(e) => setDateFilter(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
        />
      </div>

      <Table columns={columns} data={assignments} loading={loading} searchPlaceholder="Search assignments..." />

      {/* Create Assignment Modal with Pre-Validation Warnings */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Schedule Guard Assignment"
      >
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-300 uppercase mb-1">Select Officer</label>
            <select
              required
              value={formData.user_id}
              onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100"
            >
              {guards.map((g) => (
                <option key={g.id} value={g.id}>{g.name} ({g.email})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-300 uppercase mb-1">Deployment Site</label>
            <select
              required
              value={formData.site_id}
              onChange={(e) => setFormData({ ...formData, site_id: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100"
            >
              {sites.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-300 uppercase mb-1">Shift Schedule</label>
              <select
                required
                value={formData.shift_id}
                onChange={(e) => setFormData({ ...formData, shift_id: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100"
              >
                {shifts.map((sh) => (
                  <option key={sh.id} value={sh.id}>{sh.name} ({sh.start_time} - {sh.end_time})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block font-semibold text-slate-300 uppercase mb-1">Assignment Date</label>
              <input
                type="date"
                required
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100"
              />
            </div>
          </div>

          {/* Real-time Pre-Check Result Box */}
          <div className="pt-2">
            {preChecking ? (
              <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-slate-400 text-center">
                Running compliance verification...
              </div>
            ) : preCheckResult ? (
              preCheckResult.compliant ? (
                <div className="p-3 bg-emerald-950/40 rounded-lg border border-emerald-800 text-emerald-300 flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                  <span>Fully Compliant: Hours and rest periods conform to all labor and site rules.</span>
                </div>
              ) : (
                <div className="p-3 bg-amber-950/40 rounded-lg border border-amber-800 text-amber-300 space-y-2">
                  <div className="flex items-center gap-2 font-bold">
                    <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
                    <span>Compliance Warning: Proposed assignment violates configured rules</span>
                  </div>
                  <ul className="list-disc list-inside space-y-1 text-[11px] text-amber-200">
                    {preCheckResult.violations.map((v, i) => (
                      <li key={i}>{v.message}</li>
                    ))}
                  </ul>

                  {/* Override controls */}
                  <div className="mt-3 pt-3 border-t border-amber-900/60 space-y-2">
                    <label className="flex items-center gap-2 cursor-pointer font-bold text-amber-400">
                      <input
                        type="checkbox"
                        checked={formData.override_violations}
                        onChange={(e) => setFormData({ ...formData, override_violations: e.target.checked })}
                        className="rounded bg-slate-950 border-amber-700 text-amber-500"
                      />
                      <span>Authorize Administrative Override (Rule 12 Audit Log Required)</span>
                    </label>
                    {formData.override_violations && (
                      <textarea
                        required
                        rows={2}
                        value={formData.override_reason}
                        onChange={(e) => setFormData({ ...formData, override_reason: e.target.value })}
                        placeholder="State mandatory operational justification for labor rule override..."
                        className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-slate-100 placeholder-slate-500"
                      />
                    )}
                  </div>
                </div>
              )
            ) : null}
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={preCheckResult && !preCheckResult.compliant && !formData.override_violations}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg font-semibold shadow-lg shadow-blue-600/30"
            >
              Confirm & Schedule
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
