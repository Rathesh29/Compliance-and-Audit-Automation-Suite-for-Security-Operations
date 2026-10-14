import React, { useState, useEffect } from 'react';
import { FileText, Download, Plus, Calendar, FileSpreadsheet, ExternalLink } from 'lucide-react';
import api from '../services/api';
import { Table } from '../components/common/Table';
import { Badge } from '../components/common/Badge';

export const ReportsPage = () => {
  const [reports, setReports] = useState([]);
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // Form state
  const today = new Date();
  const pastWeek = new Date();
  pastWeek.setDate(today.getDate() - 7);

  const [siteId, setSiteId] = useState('');
  const [startDate, setStartDate] = useState(pastWeek.toISOString().slice(0, 10));
  const [endDate, setEndDate] = useState(today.toISOString().slice(0, 10));
  const [reportType, setReportType] = useState('COMPLIANCE');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [reps, sRes] = await Promise.all([
        api.get('/reports'),
        api.get('/sites')
      ]);
      setReports(reps || []);
      setSites(sRes || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleGenerateReport = async (e) => {
    e.preventDefault();
    setGenerating(true);
    try {
      const payload = {
        site_id: siteId ? parseInt(siteId) : null,
        date_range_start: startDate,
        date_range_end: endDate,
        report_type: reportType
      };
      await api.post('/reports/generate', payload);
      fetchData();
    } catch (err) {
      alert(err?.message || 'Report generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const columns = [
    {
      key: 'id',
      header: 'Report Ref',
      render: (r) => <span className="font-mono text-xs font-bold text-slate-300">#REP-{r.id}</span>
    },
    {
      key: 'report_type',
      header: 'Type',
      render: (r) => <Badge variant={r.report_type} label={r.report_type} />
    },
    {
      key: 'site_name',
      header: 'Facility Target',
      render: (r) => r.site_name
    },
    {
      key: 'period',
      header: 'Audit Period',
      render: (r) => <span className="font-mono text-xs">{r.date_range_start} to {r.date_range_end}</span>
    },
    {
      key: 'generated_by',
      header: 'Auditor Signatory',
      render: (r) => r.generated_by
    },
    {
      key: 'created_at',
      header: 'Compiled At',
      render: (r) => r.created_at ? r.created_at.slice(0, 16).replace('T', ' ') : '-'
    },
    {
      key: 'actions',
      header: 'Export Documents',
      render: (r) => (
        <div className="flex items-center gap-2">
          <a
            href={`http://localhost:8000/api/reports/${r.id}/pdf`}
            target="_blank"
            rel="noreferrer"
            className="px-2.5 py-1 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 rounded text-xs font-semibold flex items-center gap-1 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            PDF
          </a>
          <a
            href={`http://localhost:8000/api/reports/${r.id}/csv`}
            target="_blank"
            rel="noreferrer"
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 text-slate-300 border border-slate-700 rounded text-xs font-semibold flex items-center gap-1 transition-colors"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            CSV
          </a>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">REGULATORY AUDIT REPORT COMPILER</h2>
          <p className="text-xs text-slate-400 mt-1">
            Generate verifiable compliance dossiers, incident records, and attendance summaries for regulators and insurers.
          </p>
        </div>
      </div>

      {/* Report Generator Control Card */}
      <div className="bg-slate-850/80 border border-slate-800 rounded-xl p-5 shadow-xl">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
          Configure Audit Parameters
        </h3>
        <form onSubmit={handleGenerateReport} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
          <div>
            <label className="block text-slate-400 mb-1 font-semibold uppercase">Facility Target</label>
            <select
              value={siteId}
              onChange={(e) => setSiteId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-100"
            >
              <option value="">All Operational Sites</option>
              {sites.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-semibold uppercase">Report Dossier Type</label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-100"
            >
              <option value="COMPLIANCE">COMPLIANCE</option>
              <option value="INCIDENT">INCIDENT</option>
              <option value="ATTENDANCE_SUMMARY">ATTENDANCE_SUMMARY</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-semibold uppercase">Date Range Start</label>
            <input
              type="date"
              required
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-100"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-semibold uppercase">Date Range End</label>
            <input
              type="date"
              required
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2 text-slate-100"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={generating}
              className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold rounded-lg shadow-lg shadow-blue-600/30 flex items-center justify-center gap-1.5 transition-all"
            >
              <Plus className="w-4 h-4" />
              <span>{generating ? 'Compiling...' : 'Generate Dossier'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Historical Generated Reports Table */}
      <Table columns={columns} data={reports} loading={loading} searchPlaceholder="Search compiled reports..." />
    </div>
  );
};
