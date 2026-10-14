import React, { useState, useEffect } from 'react';
import {
  Fingerprint,
  ShieldCheck,
  FileText,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Search,
  ExternalLink
} from 'lucide-react';
import api from '../services/api';
import { Card } from '../components/common/Card';
import { ScoreRing } from '../components/common/ScoreRing';
import { Badge } from '../components/common/Badge';

export const AuditorDashboard = () => {
  const [integrity, setIntegrity] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);
  const [exceptions, setExceptions] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [logs, excs, reps, integ] = await Promise.all([
        api.get('/audit/logs?limit=8'),
        api.get('/audit/exceptions?limit=5'),
        api.get('/reports?limit=5'),
        api.get('/audit/integrity')
      ]);
      setAuditLogs(logs || []);
      setExceptions(excs || []);
      setReports(reps || []);
      setIntegrity(integ);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const runIntegrityCheck = async () => {
    setVerifying(true);
    try {
      const res = await api.get('/audit/integrity');
      setIntegrity(res);
    } catch (e) {
      alert('Integrity check failed');
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">AUDITOR SURVEILLANCE & ASSURANCE</h2>
          <p className="text-xs text-slate-400 mt-1">
            Independent read-only audit inspection, mathematical chain verification, and regulatory report exports.
          </p>
        </div>
        <button
          onClick={runIntegrityCheck}
          disabled={verifying}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-lg shadow-emerald-600/20 transition-all"
        >
          <Fingerprint className="w-4 h-4" />
          <span>{verifying ? 'Calculating SHA-256 Hashes...' : 'Verify Hash-Chain Integrity'}</span>
        </button>
      </div>

      {/* Cryptographic Chain Integrity Banner */}
      {integrity && (
        <div
          className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
            integrity.valid
              ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300'
              : 'bg-rose-950/60 border-rose-800 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-3">
            {integrity.valid ? (
              <CheckCircle className="w-6 h-6 text-emerald-400 flex-shrink-0" />
            ) : (
              <XCircle className="w-6 h-6 text-rose-400 flex-shrink-0" />
            )}
            <div>
              <h4 className="font-bold text-sm">
                {integrity.valid
                  ? 'Cryptographic Hash-Chain Intact & Valid'
                  : '⚠️ Chain Tampering Detected! Invalid Blocks Found!'}
              </h4>
              <p className="text-xs opacity-90 mt-0.5 font-mono">
                Verified: {integrity.records_checked} sequential records • Genesis Hash: Anchored (SHA-256)
              </p>
            </div>
          </div>
          <div className="text-xs font-mono bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800 self-start sm:self-center">
            Chain Head: {integrity.chain_head ? `${integrity.chain_head.slice(0, 16)}...` : 'ROOT'}
          </div>
        </div>
      )}

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card
          title="Verified Records"
          value={integrity?.records_checked || 0}
          subtitle="Immutable Append-Only Entries"
          icon={Fingerprint}
          color="emerald"
        />
        <Card
          title="Active Exceptions"
          value={exceptions.filter((e) => e.status === 'OPEN').length}
          subtitle="Flagged by Engine"
          icon={AlertTriangle}
          color="amber"
        />
        <Card
          title="Generated Reports"
          value={reports.length}
          subtitle="Signed PDF & CSV Exports"
          icon={FileText}
          color="blue"
        />
        <Card
          title="Audit Permissions"
          value="READ-ONLY"
          subtitle="Modifications Disallowed by Policy"
          icon={ShieldCheck}
          color="purple"
        />
      </div>

      {/* Main Grid: Immutable Logs Explorer & Recent Reports */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Audit Logs with Hashes */}
        <div className="lg:col-span-2 bg-slate-850/80 border border-slate-800 rounded-xl p-5 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
              Immutable Audit Log Trail (Live Chained)
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">SHA-256 Chained</span>
          </div>
          <div className="space-y-2 overflow-x-auto">
            {auditLogs.map((log) => (
              <div
                key={log.id}
                className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg text-xs space-y-1 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-200">#{log.id} {log.action}</span>
                    <Badge variant={log.entity_type} label={log.entity_type} />
                  </div>
                  <span className="text-slate-500 font-mono text-[10px]">{log.timestamp}</span>
                </div>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-[11px] text-slate-400">
                  <span>Officer: <b className="text-slate-300">{log.performed_by}</b></span>
                  <span className="font-mono text-[10px] text-slate-500 truncate max-w-xs">
                    Hash: <span className="text-emerald-400">{log.record_hash}</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Reports Archive */}
        <div className="bg-slate-850/80 border border-slate-800 rounded-xl p-5 shadow-xl flex flex-col">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">
            Official Regulatory Reports
          </h3>
          <div className="flex-1 space-y-3 overflow-y-auto">
            {reports.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-8">No reports compiled yet.</p>
            ) : (
              reports.map((rep) => (
                <div
                  key={rep.id}
                  className="p-3 bg-slate-900/80 border border-slate-800 rounded-lg text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-200">{rep.site_name}</span>
                    <Badge variant="COMPLIANCE" label={rep.report_type} />
                  </div>
                  <p className="text-slate-400 text-[11px]">Period: {rep.date_range_start} to {rep.date_range_end}</p>
                  <p className="text-slate-500 text-[10px]">Compiled by: {rep.generated_by}</p>
                  <div className="pt-2 flex items-center gap-2">
                    <a
                      href={`http://localhost:8000/api/reports/${rep.id}/pdf`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-2.5 py-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 rounded text-[10px] font-semibold flex items-center gap-1 transition-colors"
                    >
                      <FileText className="w-3 h-3" />
                      PDF
                    </a>
                    <a
                      href={`http://localhost:8000/api/reports/${rep.id}/csv`}
                      target="_blank"
                      rel="noreferrer"
                      className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded text-[10px] font-semibold flex items-center gap-1 transition-colors"
                    >
                      <ExternalLink className="w-3 h-3" />
                      CSV
                    </a>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
