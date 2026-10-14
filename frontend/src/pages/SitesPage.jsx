import React, { useState, useEffect } from 'react';
import { MapPin, Plus, QrCode, Sliders, Edit2, Shield, Download } from 'lucide-react';
import api from '../services/api';
import { Table } from '../components/common/Table';
import { Badge } from '../components/common/Badge';
import { Modal } from '../components/common/Modal';
import { ScoreRing } from '../components/common/ScoreRing';
import { useAuth } from '../context/AuthContext';

export const SitesPage = () => {
  const { isAdmin } = useAuth();
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [siteModalOpen, setSiteModalOpen] = useState(false);
  const [qrModalOpen, setQrModalOpen] = useState(false);
  const [rulesModalOpen, setRulesModalOpen] = useState(false);
  const [selectedSite, setSelectedSite] = useState(null);
  const [qrData, setQrData] = useState(null);

  // Form state for Site Create / Edit
  const [formData, setFormData] = useState({
    name: '',
    location_name: '',
    latitude: 37.7749,
    longitude: -122.4194,
    radius_meters: 150.0
  });

  // Compliance rules state
  const [rulesData, setRulesData] = useState({
    max_daily_hours: 12.0,
    minimum_rest_hours: 8.0,
    max_weekly_hours: 60.0,
    allow_overtime: false,
    require_qr: true,
    require_gps: true,
    late_threshold_minutes: 10
  });

  const fetchSites = async () => {
    try {
      setLoading(true);
      const res = await api.get('/sites');
      setSites(res || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSites();
  }, []);

  const handleOpenCreate = () => {
    setSelectedSite(null);
    setFormData({
      name: '',
      location_name: '',
      latitude: 37.7749,
      longitude: -122.4194,
      radius_meters: 150.0
    });
    setSiteModalOpen(true);
  };

  const handleOpenEdit = (site) => {
    setSelectedSite(site);
    setFormData({
      name: site.name,
      location_name: site.location_name,
      latitude: site.latitude,
      longitude: site.longitude,
      radius_meters: site.radius_meters
    });
    setSiteModalOpen(true);
  };

  const handleOpenQR = async (site) => {
    try {
      const data = await api.get(`/sites/${site.id}/qr`);
      setQrData(data);
      setSelectedSite(site);
      setQrModalOpen(true);
    } catch (e) {
      alert(e?.message || 'Failed to load QR code');
    }
  };

  const handleOpenRules = (site) => {
    setSelectedSite(site);
    setRulesData(site.compliance_rules || {
      max_daily_hours: 12.0,
      minimum_rest_hours: 8.0,
      max_weekly_hours: 60.0,
      allow_overtime: false,
      require_qr: true,
      require_gps: true,
      late_threshold_minutes: 10
    });
    setRulesModalOpen(true);
  };

  const handleSiteSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedSite) {
        await api.put(`/sites/${selectedSite.id}`, formData);
      } else {
        await api.post('/sites', formData);
      }
      setSiteModalOpen(false);
      fetchSites();
    } catch (err) {
      alert(err?.message || 'Failed to save site');
    }
  };

  const handleRulesSubmit = async (e) => {
    e.preventDefault();
    if (!selectedSite) return;
    try {
      await api.put(`/sites/${selectedSite.id}`, { compliance_rules: rulesData });
      setRulesModalOpen(false);
      fetchSites();
    } catch (err) {
      alert(err?.message || 'Failed to update rules');
    }
  };

  const columns = [
    {
      key: 'name',
      header: 'Facility & Location',
      render: (s) => (
        <div>
          <span className="font-bold text-slate-100">{s.name}</span>
          <span className="block text-slate-400 text-xs flex items-center gap-1 mt-0.5">
            <MapPin className="w-3 h-3 text-blue-400" />
            {s.location_name}
          </span>
        </div>
      )
    },
    {
      key: 'coordinates',
      header: 'Geofence Boundaries',
      render: (s) => (
        <span className="font-mono text-xs text-slate-300">
          {s.latitude.toFixed(4)}, {s.longitude.toFixed(4)} ({s.radius_meters}m)
        </span>
      )
    },
    {
      key: 'compliance_score',
      header: 'Compliance Rating',
      render: (s) => (
        <span className={`font-bold text-xs px-2 py-0.5 rounded-full border ${
          s.compliance_score >= 90 ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800' :
          s.compliance_score >= 75 ? 'bg-blue-950/60 text-blue-400 border-blue-800' :
          'bg-amber-950/60 text-amber-400 border-amber-800'
        }`}>
          {s.compliance_score}%
        </span>
      )
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (s) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleOpenQR(s)}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 text-emerald-400 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors"
            title="Inspect Site QR Code"
          >
            <QrCode className="w-3.5 h-3.5" />
            QR
          </button>
          <button
            onClick={() => handleOpenRules(s)}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 text-purple-400 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors"
            title="Configure Rules"
          >
            <Sliders className="w-3.5 h-3.5" />
            Rules
          </button>
          {isAdmin && (
            <button
              onClick={() => handleOpenEdit(s)}
              className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
              title="Edit Site Details"
            >
              <Edit2 className="w-4 h-4" />
            </button>
          )}
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-black text-white tracking-tight">OPERATIONAL SITES & GEOFENCES</h2>
          <p className="text-xs text-slate-400 mt-1">
            Site coordinates, Haversine GPS radius parameters, QR tokens, and contractual labor limits.
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={handleOpenCreate}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-lg shadow-blue-600/20 transition-all self-start sm:self-auto"
          >
            <Plus className="w-4 h-4" />
            <span>Register Facility</span>
          </button>
        )}
      </div>

      {/* Sites Table */}
      <Table columns={columns} data={sites} loading={loading} searchPlaceholder="Search facility name or location..." />

      {/* Site Create/Edit Modal */}
      <Modal
        isOpen={siteModalOpen}
        onClose={() => setSiteModalOpen(false)}
        title={selectedSite ? `Edit Site: ${selectedSite.name}` : 'Register New Security Site'}
      >
        <form onSubmit={handleSiteSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Facility Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:border-blue-500"
              placeholder="e.g. Corporate Tower Headquarters"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Physical Address / Gate</label>
            <input
              type="text"
              required
              value={formData.location_name}
              onChange={(e) => setFormData({ ...formData, location_name: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 focus:border-blue-500"
              placeholder="e.g. 742 Evergreen Plaza, Gate 1"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Latitude</label>
              <input
                type="number"
                step="any"
                required
                value={formData.latitude}
                onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Longitude</label>
              <input
                type="number"
                step="any"
                required
                value={formData.longitude}
                onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">
              Geofence Radius (Meters)
            </label>
            <input
              type="number"
              step="any"
              required
              value={formData.radius_meters}
              onChange={(e) => setFormData({ ...formData, radius_meters: parseFloat(e.target.value) })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 font-mono"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setSiteModalOpen(false)}
              className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold"
            >
              {selectedSite ? 'Save Changes' : 'Create Site'}
            </button>
          </div>
        </form>
      </Modal>

      {/* QR Code Inspection Modal */}
      <Modal isOpen={qrModalOpen} onClose={() => setQrModalOpen(false)} title="Site Verification QR Code">
        {qrData && (
          <div className="flex flex-col items-center justify-center p-4 text-center space-y-4">
            <div className="p-3 bg-white rounded-2xl shadow-xl">
              <img src={qrData.qr_code_base64} alt="Site QR" className="w-56 h-56 object-contain" />
            </div>
            <div className="w-full p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs">
              <span className="text-slate-400 block font-semibold mb-1">Encrypted Site Verification Token</span>
              <code className="text-emerald-400 font-mono select-all text-sm block overflow-x-auto">
                {qrData.qr_token}
              </code>
            </div>
            <a
              href={qrData.qr_code_base64}
              download={`${selectedSite?.name || 'site'}_qr.png`}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold flex items-center gap-2 shadow-lg shadow-emerald-600/20"
            >
              <Download className="w-4 h-4" />
              Download Printable Poster PNG
            </a>
          </div>
        )}
      </Modal>

      {/* Compliance Rules Modal */}
      <Modal
        isOpen={rulesModalOpen}
        onClose={() => setRulesModalOpen(false)}
        title={`Compliance Rules: ${selectedSite?.name}`}
      >
        <form onSubmit={handleRulesSubmit} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-300 uppercase mb-1">Max Daily Hours</label>
              <input
                type="number"
                step="0.5"
                value={rulesData.max_daily_hours}
                onChange={(e) => setRulesData({ ...rulesData, max_daily_hours: parseFloat(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-300 uppercase mb-1">Minimum Rest Hours</label>
              <input
                type="number"
                step="0.5"
                value={rulesData.minimum_rest_hours}
                onChange={(e) => setRulesData({ ...rulesData, minimum_rest_hours: parseFloat(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-300 uppercase mb-1">Max Weekly Hours</label>
              <input
                type="number"
                step="1"
                value={rulesData.max_weekly_hours}
                onChange={(e) => setRulesData({ ...rulesData, max_weekly_hours: parseFloat(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-300 uppercase mb-1">Grace Period (Minutes)</label>
              <input
                type="number"
                step="1"
                value={rulesData.late_threshold_minutes}
                onChange={(e) => setRulesData({ ...rulesData, late_threshold_minutes: parseInt(e.target.value) })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-slate-100"
              />
            </div>
          </div>

          <div className="pt-2 space-y-2 border-t border-slate-800">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={rulesData.require_gps}
                onChange={(e) => setRulesData({ ...rulesData, require_gps: e.target.checked })}
                className="rounded bg-slate-950 border-slate-700 text-blue-600 focus:ring-0"
              />
              <span className="text-slate-200">Enforce GPS Haversine Geofence Checking</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={rulesData.require_qr}
                onChange={(e) => setRulesData({ ...rulesData, require_qr: e.target.checked })}
                className="rounded bg-slate-950 border-slate-700 text-blue-600 focus:ring-0"
              />
              <span className="text-slate-200">Enforce Physical Site QR Token Verification</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={rulesData.allow_overtime}
                onChange={(e) => setRulesData({ ...rulesData, allow_overtime: e.target.checked })}
                className="rounded bg-slate-950 border-slate-700 text-blue-600 focus:ring-0"
              />
              <span className="text-slate-200">Permit Overtime Without Compliance Flagging</span>
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setRulesModalOpen(false)}
              className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-semibold shadow-lg shadow-purple-600/30"
            >
              Update Compliance Rules
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
