import React, { useState, useEffect } from 'react';
import {
  Fingerprint,
  CheckCircle,
  XCircle,
  Search,
  RefreshCw,
  ShieldAlert,
  Hash,
  Database
} from 'lucide-react';
import api from '../services/api';
import { Table } from '../components/common/Table';
import { Badge } from '../components/common/Badge';

export const AuditPage = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [integrity, setIntegrity] = useState(null);
  const [verifying, setVerifying] = useState(false);

  // Filters
  const [entityFilter, setEntityFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');

  const fetchAuditLogs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (entityFilter) params.append('entity', entityFilter);
      if (actionFilter) params.append('action', actionFilter);

      const [logsRes, integRes] = await Promise.all([
        api.get(`/audit/logs?limit=200&${params.toString()}`),
        api.get('/audit/integrity')
      ]);
      setLogs(logsRes || []);
      setIntegrity(integRes);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [entityFilter, actionFilter]);

  const handleVerifyIntegrity = async () => {
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

  const columns = [
    {
      key: 'id',
      header: 'Block #',
      render: (l) => <span className="font-mono text-xs font-bold text-slate-400">#{l.id}</span>
    },
    {
      key: 'timestamp',
      header: 'UTC Timestamp',
      render: (l) => (
        <span className="font-mono text-xs text-slate-300">
          {l.timestamp ? l.timestamp.replace('T', ' ').slice(0, 19) : '-'}
        </span>
      )
    },
    {
      key: 'entity',
      header: 'Entity / Target',
      render: (l) => (
        <div>
          <Badge variant={l.entity_type} label={l.entity_type} />
          <span className="text-slate-400 text-xs ml-1.5 font-mono">#{l.entity_id}</span>
        </div>
      )
    },
    {
      key: 'action',
      header: 'Action Executed',
      render: (l) => <span className="font-bold text-slate-100">{l.action}</span>
    },
    {
      key: 'performed_by',
      header: 'Signatory / Actor',
      render: (l) => <span className="text-xs text-slate-300">{l.performed_by}</span>
    },
    {
      key: 'record_hash',
      header: 'Cryptographic SHA-256 Hash',
      render: (l) => (
        <div className="font-mono text-[11px] text-emerald-400 truncate max-w-xs" title={`Parent: ${l.previous_hash}\nHash: ${l.record_hash}`}>
          {l.record_hash.slice(0, 18)}...
        </div>
      )
    },
    {
      key: 'metadata',
      header: 'Context Metadata',
      render: (l) => (
        <span className="text-[11px] text-slate-400 font-mono truncate max-w-xs block" title={JSON.stringify(l.metadata)}>
          {JSON.stringify(l.metadata || {})}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">IMMUTABLE AUDIT EXPLORER</h2>
          <p className="text-xs text-slate-400 mt-1">
            Tamper-evident append-only ledger secured by SHA-256 parent hash chaining.
          </p>
        </div>
        <button
          onClick={handleVerifyIntegrity}
          disabled={verifying}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-lg shadow-emerald-600/20 transition-all self-start sm:self-auto"
        >
          <Fingerprint className="w-4 h-4" />
          <span>{verifying ? 'Verifying Chain...' : 'Verify Cryptographic Integrity'}</span>
        </button>
      </div>

      {/* Chain Status Card */}
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
                {integrity.valid ? 'Cryptographic Hash-Chain Intact & Valid' : 'TAMPERING DETECTED IN AUDIT LEDGER'}
              </h4>
              <p className="text-xs opacity-90 mt-0.5 font-mono">
                {integrity.records_checked} sequential records cryptographically verified from Genesis Hash.
              </p>
            </div>
          </div>
          <div className="text-xs font-mono bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800 self-start sm:self-center">
            Chain Head: {integrity.chain_head ? `${integrity.chain_head.slice(0, 16)}...` : 'ROOT'}
          </div>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-850/60 p-3 rounded-xl border border-slate-800">
        <select
          value={entityFilter}
          onChange={(e) => setEntityFilter(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
        >
          <option value="">All Entities</option>
          <option value="AUTH">AUTH</option>
          <option value="USER">USER</option>
          <option value="SITE">SITE</option>
          <option value="SHIFT">SHIFT</option>
          <option value="ASSIGNMENT">ASSIGNMENT</option>
          <option value="ATTENDANCE">ATTENDANCE</option>
          <option value="EXCEPTION">EXCEPTION</option>
          <option value="REPORT">REPORT</option>
        </select>

        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
        >
          <option value="">All Actions</option>
          <option value="LOGIN_SUCCESS">LOGIN_SUCCESS</option>
          <option value="LOGIN_FAILED">LOGIN_FAILED</option>
          <option value="CHECK_IN">CHECK_IN</option>
          <option value="CHECK_OUT">CHECK_OUT</option>
          <option value="LATE_CHECKIN">LATE_CHECKIN</option>
          <option value="MISSED_SHIFT">MISSED_SHIFT</option>
          <option value="ADMIN_OVERRIDE">ADMIN_OVERRIDE</option>
          <option value="EXCEPTION_RESOLVED">EXCEPTION_RESOLVED</option>
          <option value="REPORT_GENERATED">REPORT_GENERATED</option>
        </select>
      </div>

      <Table columns={columns} data={logs} loading={loading} searchPlaceholder="Search audit trail..." />
    </div>
  );
};
