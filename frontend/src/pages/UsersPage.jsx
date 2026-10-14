import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Search, Edit2, Shield, UserX, UserCheck } from 'lucide-react';
import api from '../services/api';
import { Table } from '../components/common/Table';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';

export const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'GUARD',
    phone: '',
    status: 'ACTIVE'
  });

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (roleFilter) params.append('role', roleFilter);
      if (statusFilter) params.append('status', statusFilter);
      const res = await api.get(`/users?${params.toString()}`);
      setUsers(res || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [roleFilter, statusFilter]);

  const handleOpenCreate = () => {
    setEditingUser(null);
    setFormData({
      name: '',
      email: '',
      password: '',
      role: 'GUARD',
      phone: '',
      status: 'ACTIVE'
    });
    setModalOpen(true);
  };

  const handleOpenEdit = (user) => {
    setEditingUser(user);
    setFormData({
      name: user.name,
      email: user.email,
      password: '',
      role: user.role,
      phone: user.phone || '',
      status: user.status
    });
    setModalOpen(true);
  };

  const handleToggleStatus = async (user) => {
    const nextStatus = user.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    try {
      await api.put(`/users/${user.id}`, { status: nextStatus });
      fetchUsers();
    } catch (e) {
      alert(e?.message || 'Failed to update user status');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingUser) {
        const payload = {
          name: formData.name,
          email: formData.email,
          role: formData.role,
          phone: formData.phone,
          status: formData.status
        };
        if (formData.password.trim()) payload.password = formData.password;
        await api.put(`/users/${editingUser.id}`, payload);
      } else {
        await api.post('/users', formData);
      }
      setModalOpen(false);
      fetchUsers();
    } catch (err) {
      alert(err?.message || 'Failed to save user');
    }
  };

  const columns = [
    {
      key: 'name',
      header: 'Officer / User',
      render: (u) => (
        <div>
          <span className="font-bold text-slate-100">{u.name}</span>
          <span className="block text-slate-400 text-xs">{u.email}</span>
        </div>
      )
    },
    {
      key: 'role',
      header: 'Role (RBAC)',
      render: (u) => <Badge variant={u.role} label={u.role} />
    },
    {
      key: 'status',
      header: 'Account Status',
      render: (u) => <Badge variant={u.status} label={u.status} />
    },
    {
      key: 'phone',
      header: 'Contact Phone',
      render: (u) => u.phone || '-'
    },
    {
      key: 'created_at',
      header: 'Enrolled Date',
      render: (u) => u.created_at ? u.created_at.slice(0, 10) : '-'
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (u) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleOpenEdit(u)}
            className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
            title="Edit User"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => handleToggleStatus(u)}
            className={`p-1.5 rounded-lg transition-colors ${
              u.status === 'ACTIVE'
                ? 'text-slate-400 hover:text-rose-400 hover:bg-slate-800'
                : 'text-slate-400 hover:text-emerald-400 hover:bg-slate-800'
            }`}
            title={u.status === 'ACTIVE' ? 'Deactivate' : 'Activate'}
          >
            {u.status === 'ACTIVE' ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">SECURITY PERSONNEL & USER DIRECTORY</h2>
          <p className="text-xs text-slate-400 mt-1">
            Role-based credentials, biometric status, and access privilege administration.
          </p>
        </div>
        <button
          onClick={handleOpenCreate}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-lg shadow-blue-600/20 transition-all self-start sm:self-auto"
        >
          <UserPlus className="w-4 h-4" />
          <span>Enroll New Officer</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
        >
          <option value="">All Roles</option>
          <option value="ADMIN">ADMIN</option>
          <option value="SUPERVISOR">SUPERVISOR</option>
          <option value="AUDITOR">AUDITOR</option>
          <option value="GUARD">GUARD</option>
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-slate-850 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
        >
          <option value="">All Statuses</option>
          <option value="ACTIVE">ACTIVE</option>
          <option value="INACTIVE">INACTIVE</option>
        </select>
      </div>

      {/* Users Table */}
      <Table columns={columns} data={users} loading={loading} searchPlaceholder="Search by name or email..." />

      {/* Create / Edit Modal */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingUser ? `Edit Officer: ${editingUser.name}` : 'Enroll New Security Officer'}
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Full Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Email Address</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
              {editingUser ? 'Password (leave blank to keep unchanged)' : 'Initial Password'}
            </label>
            <input
              type="password"
              required={!editingUser}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:border-blue-500"
              placeholder="••••••••••••"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Role (RBAC)</label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:border-blue-500"
              >
                <option value="GUARD">GUARD</option>
                <option value="SUPERVISOR">SUPERVISOR</option>
                <option value="AUDITOR">AUDITOR</option>
                <option value="ADMIN">ADMIN</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Status</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:border-blue-500"
              >
                <option value="ACTIVE">ACTIVE</option>
                <option value="INACTIVE">INACTIVE</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Phone Number</label>
            <input
              type="text"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              placeholder="+1-555-0199"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:border-blue-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-750 text-slate-300 rounded-lg text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-blue-600/30"
            >
              {editingUser ? 'Save Changes' : 'Enroll Officer'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
