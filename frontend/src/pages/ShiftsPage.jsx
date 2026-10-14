import React, { useState, useEffect } from 'react';
import { Clock, Plus, Moon, Sun, Edit2 } from 'lucide-react';
import api from '../services/api';
import { Table } from '../components/common/Table';
import { Modal } from '../components/common/Modal';
import { useAuth } from '../context/AuthContext';

export const ShiftsPage = () => {
  const { isAdmin, isSupervisor } = useAuth();
  const [shifts, setShifts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingShift, setEditingShift] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    start_time: '08:00',
    end_time: '16:00',
    grace_period_minutes: 15
  });

  const fetchShifts = async () => {
    try {
      setLoading(true);
      const res = await api.get('/shifts');
      setShifts(res || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShifts();
  }, []);

  const handleOpenCreate = () => {
    setEditingShift(null);
    setFormData({
      name: '',
      start_time: '08:00',
      end_time: '16:00',
      grace_period_minutes: 15
    });
    setModalOpen(true);
  };

  const handleOpenEdit = (shift) => {
    setEditingShift(shift);
    setFormData({
      name: shift.name,
      start_time: shift.start_time,
      end_time: shift.end_time,
      grace_period_minutes: shift.grace_period_minutes
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingShift) {
        await api.put(`/shifts/${editingShift.id}`, formData);
      } else {
        await api.post('/shifts', formData);
      }
      setModalOpen(false);
      fetchShifts();
    } catch (err) {
      alert(err?.message || 'Failed to save shift');
    }
  };

  const columns = [
    {
      key: 'name',
      header: 'Shift Title',
      render: (s) => (
        <div className="flex items-center gap-2">
          {s.is_overnight ? (
            <Moon className="w-4 h-4 text-indigo-400 flex-shrink-0" />
          ) : (
            <Sun className="w-4 h-4 text-amber-400 flex-shrink-0" />
          )}
          <span className="font-bold text-slate-100">{s.name}</span>
        </div>
      )
    },
    {
      key: 'hours',
      header: 'Schedule Hours',
      render: (s) => (
        <span className="font-mono text-xs text-slate-300">
          {s.start_time} — {s.end_time} ({s.duration_hours}h)
        </span>
      )
    },
    {
      key: 'is_overnight',
      header: 'Shift Type',
      render: (s) => (
        <span className={`text-xs px-2.5 py-0.5 rounded-full border ${
          s.is_overnight
            ? 'bg-indigo-950/60 text-indigo-300 border-indigo-800'
            : 'bg-amber-950/60 text-amber-300 border-amber-800'
        }`}>
          {s.is_overnight ? '🌙 Overnight' : '☀️ Day Shift'}
        </span>
      )
    },
    {
      key: 'grace_period_minutes',
      header: 'Grace Window',
      render: (s) => `${s.grace_period_minutes} Minutes`
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (s) => (
        (isAdmin || isSupervisor) && (
          <button
            onClick={() => handleOpenEdit(s)}
            className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <Edit2 className="w-4 h-4" />
          </button>
        )
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">OPERATIONAL SHIFT DEFINITIONS</h2>
          <p className="text-xs text-slate-400 mt-1">
            Standard and overnight guard rotations with automated grace threshold enforcement.
          </p>
        </div>
        {(isAdmin || isSupervisor) && (
          <button
            onClick={handleOpenCreate}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-lg shadow-blue-600/20 self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Create Shift Schedule</span>
          </button>
        )}
      </div>

      <Table columns={columns} data={shifts} loading={loading} searchPlaceholder="Search shifts..." />

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingShift ? `Edit Shift: ${editingShift.name}` : 'Create Shift Schedule'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Shift Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:border-blue-500"
              placeholder="e.g. Day Sentinel Rotation"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Start Time (HH:MM)</label>
              <input
                type="text"
                pattern="^([01]\d|2[0-3]):([0-5]\d)$"
                required
                value={formData.start_time}
                onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 font-mono"
                placeholder="08:00"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">End Time (HH:MM)</label>
              <input
                type="text"
                pattern="^([01]\d|2[0-3]):([0-5]\d)$"
                required
                value={formData.end_time}
                onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 font-mono"
                placeholder="16:00"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
              Grace Period Allowed (Minutes)
            </label>
            <input
              type="number"
              min="0"
              max="60"
              required
              value={formData.grace_period_minutes}
              onChange={(e) => setFormData({ ...formData, grace_period_minutes: parseInt(e.target.value) })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 font-mono"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold"
            >
              {editingShift ? 'Save Changes' : 'Create Shift'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
