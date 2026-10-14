import React, { useState, useEffect } from 'react';
import { CheckCircle2, Clock, MapPin, QrCode, AlertCircle, RefreshCw } from 'lucide-react';
import api from '../services/api';
import { Table } from '../components/common/Table';
import { Badge } from '../components/common/Badge';

export const AttendancePage = () => {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  const fetchAttendance = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      const res = await api.get(`/assignments?${params.toString()}`);
      setAssignments(res || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttendance();
  }, [statusFilter]);

  const columns = [
    {
      key: 'user_name',
      header: 'Officer',
      render: (a) => (
        <div>
          <span className="font-bold text-slate-100">{a.user_name}</span>
          <span className="block text-slate-400 text-xs">{a.user_email}</span>
        </div>
      )
    },
    {
      key: 'site_name',
      header: 'Deployment Facility',
      render: (a) => a.site_name
    },
    {
      key: 'shift_name',
      header: 'Assigned Schedule',
      render: (a) => `${a.shift_name} (${a.shift_start} - ${a.shift_end})`
    },
    {
      key: 'date',
      header: 'Date',
      render: (a) => <span className="font-mono text-xs">{a.date}</span>
    },
    {
      key: 'status',
      header: 'Attendance Status',
      render: (a) => <Badge variant={a.status} label={a.status} />
    },
    {
      key: 'compliance_violations',
      header: 'Violations / Breach Reason',
      render: (a) => (
        a.compliance_violations && a.compliance_violations.length > 0 ? (
          <div className="space-y-0.5">
            {a.compliance_violations.map((v, i) => (
              <span key={i} className="block text-xs text-rose-400 font-medium">
                • {v.message || v.type}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-xs text-emerald-400">Normal / On-Schedule</span>
        )
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">ATTENDANCE & TIME-VERIFICATION CONSOLE</h2>
          <p className="text-xs text-slate-400 mt-1">
            Validated check-in and check-out logs cross-verified against GPS coordinates and site QR keys.
          </p>
        </div>
        <button
          onClick={fetchAttendance}
          className="px-3.5 py-1.5 bg-slate-850 hover:bg-slate-800 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-2 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Records</span>
        </button>
      </div>

      <div className="flex items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
        >
          <option value="">All Attendance Statuses</option>
          <option value="CHECKED_IN">CHECKED_IN (On Duty)</option>
          <option value="COMPLETED">COMPLETED (Shift Concluded)</option>
          <option value="MISSED">MISSED (Unreported)</option>
          <option value="SCHEDULED">SCHEDULED (Pending)</option>
        </select>
      </div>

      <Table columns={columns} data={assignments} loading={loading} searchPlaceholder="Search attendance logs..." />
    </div>
  );
};
