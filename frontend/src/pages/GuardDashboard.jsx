import React, { useState, useEffect } from 'react';
import {
  MapPin,
  QrCode,
  Clock,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  Radio,
  Navigation,
  LogOut,
  LogIn
} from 'lucide-react';
import api from '../services/api';
import { Badge } from '../components/common/Badge';
import { Card } from '../components/common/Card';
import { useAuth } from '../context/AuthContext';

export const GuardDashboard = () => {
  const { user } = useAuth();
  const [assignments, setAssignments] = useState([]);
  const [selectedAsg, setSelectedAsg] = useState(null);
  const [coords, setCoords] = useState({ lat: null, lon: null });
  const [geoStatus, setGeoStatus] = useState('Idle');
  const [qrToken, setQrToken] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchGuardAssignments = async () => {
    try {
      setLoading(true);
      const res = await api.get('/attendance/status');
      setAssignments(res || []);
      if (res && res.length > 0) {
        setSelectedAsg(res[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGuardAssignments();
  }, []);

  // Request browser geolocation
  const handleAcquireLocation = () => {
    setGeoStatus('Locating device...');
    if (!navigator.geolocation) {
      setGeoStatus('Geolocation not supported by browser. Using site coordinate.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({
          lat: position.coords.latitude,
          lon: position.coords.longitude
        });
        setGeoStatus(`Acquired: ${position.coords.latitude.toFixed(5)}, ${position.coords.longitude.toFixed(5)}`);
      },
      (error) => {
        // Fallback for demo: use test coordinates
        setGeoStatus(`Location request: ${error.message}. (Use simulated coords)`);
        setCoords({ lat: 37.774929, lon: -122.419416 });
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  // Perform Check-in
  const handleCheckIn = async () => {
    if (!selectedAsg) return;
    setFeedback(null);
    setActionLoading(true);

    try {
      const lat = coords.lat ?? 37.774929;
      const lon = coords.lon ?? -122.419416;

      const res = await api.post('/attendance/check-in', {
        assignment_id: selectedAsg.assignment_id,
        latitude: lat,
        longitude: lon,
        qr_token: qrToken.trim()
      });

      setFeedback({
        type: 'success',
        message: 'Check-in recorded successfully! Status is now ON DUTY.'
      });
      fetchGuardAssignments();
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err?.message || 'Check-in validation failed.'
      });
    } finally {
      setActionLoading(false);
    }
  };

  // Perform Check-out
  const handleCheckOut = async () => {
    if (!selectedAsg) return;
    setFeedback(null);
    setActionLoading(true);

    try {
      const lat = coords.lat ?? 37.774929;
      const lon = coords.lon ?? -122.419416;

      const res = await api.post('/attendance/check-out', {
        assignment_id: selectedAsg.assignment_id,
        latitude: lat,
        longitude: lon,
        qr_token: qrToken.trim()
      });

      setFeedback({
        type: 'success',
        message: 'Check-out completed! Shift hours logged and audited.'
      });
      fetchGuardAssignments();
    } catch (err) {
      setFeedback({
        type: 'error',
        message: err?.message || 'Check-out failed.'
      });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Officer Header */}
      <div className="bg-slate-850/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 bg-blue-950/60 px-2.5 py-1 rounded-full border border-blue-800/60">
            Active Officer Console
          </span>
          <h2 className="text-2xl font-black text-white mt-2">{user?.name}</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Badge: <b className="text-slate-200">{user?.email}</b> • Status: <b className="text-emerald-400">ACTIVE</b>
          </p>
        </div>
        <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center gap-3">
          <Radio className="w-6 h-6 text-emerald-400 animate-pulse" />
          <div className="text-left text-xs">
            <span className="text-slate-400 block font-semibold">Dispatch Signal</span>
            <span className="text-emerald-400 font-bold">CONNECTED</span>
          </div>
        </div>
      </div>

      {feedback && (
        <div
          className={`p-4 rounded-xl text-xs font-semibold flex items-center gap-3 ${
            feedback.type === 'success'
              ? 'bg-emerald-950/80 border border-emerald-800 text-emerald-300'
              : 'bg-rose-950/80 border border-rose-800 text-rose-300'
          }`}
        >
          {feedback.type === 'success' ? (
            <CheckCircle className="w-5 h-5 flex-shrink-0 text-emerald-400" />
          ) : (
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Assignment Selection & Verification Form */}
      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-500"></div>
        </div>
      ) : assignments.length === 0 ? (
        <div className="bg-slate-850/80 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
          <Clock className="w-12 h-12 mx-auto text-slate-600 mb-3" />
          <h3 className="text-base font-bold text-slate-200">No Assignments Today</h3>
          <p className="text-xs mt-1">You do not currently have any scheduled shifts for today.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Shift Details Card */}
          <div className="bg-slate-850/80 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400">
                Assigned Post & Schedule
              </h3>
              <Badge variant={selectedAsg?.status} label={selectedAsg?.status} />
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-400 block font-semibold">Deployment Facility</span>
                <span className="text-base font-bold text-slate-100 flex items-center gap-1.5 mt-0.5">
                  <MapPin className="w-4 h-4 text-blue-400" />
                  {selectedAsg?.site_name}
                </span>
              </div>

              <div>
                <span className="text-slate-400 block font-semibold">Shift Schedule</span>
                <span className="text-sm font-bold text-slate-200 flex items-center gap-1.5 mt-0.5">
                  <Clock className="w-4 h-4 text-purple-400" />
                  {selectedAsg?.shift_name} ({selectedAsg?.shift_start} - {selectedAsg?.shift_end})
                </span>
              </div>

              {selectedAsg?.check_in_time && (
                <div className="p-3 bg-slate-900 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block">Logged Check-In</span>
                  <span className="text-emerald-400 font-mono font-bold mt-0.5">
                    {new Date(selectedAsg.check_in_time).toLocaleTimeString()}
                  </span>
                </div>
              )}

              {selectedAsg?.violations && selectedAsg.violations.length > 0 && (
                <div className="p-3 bg-amber-950/40 rounded-lg border border-amber-800/60 text-amber-300">
                  <span className="font-bold block mb-1">Compliance Flags on Record:</span>
                  <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                    {selectedAsg.violations.map((v, i) => (
                      <li key={i}>{v}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Verification Console: GPS + QR */}
          <div className="bg-slate-850/80 border border-slate-800 rounded-xl p-6 shadow-xl space-y-5">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-3">
              Biometric / Verification Actions
            </h3>

            {/* GPS Geofence Module */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 uppercase">
                  <Navigation className="w-3.5 h-3.5 text-blue-400" />
                  1. Geofence Location Verification
                </label>
                <button
                  type="button"
                  onClick={handleAcquireLocation}
                  className="px-2.5 py-1 bg-slate-800 hover:bg-slate-750 text-blue-400 border border-slate-700 rounded text-[11px] font-bold transition-colors"
                >
                  Acquire GPS
                </button>
              </div>
              <div className="p-2.5 bg-slate-950 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-400">
                {geoStatus}
              </div>
            </div>

            {/* QR Token Verification Module */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5 uppercase">
                <QrCode className="w-3.5 h-3.5 text-emerald-400" />
                2. On-Site QR Token
              </label>
              <input
                type="text"
                value={qrToken}
                onChange={(e) => setQrToken(e.target.value)}
                placeholder="Scan or input Site QR token (e.g. SITE-SEC-CORP-TOWER-7749)"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:border-emerald-500"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setQrToken('SITE-SEC-CORP-TOWER-7749')}
                  className="text-[10px] text-slate-400 hover:text-slate-200 underline"
                >
                  Fill Corporate QR
                </button>
                <button
                  type="button"
                  onClick={() => setQrToken('SITE-SEC-IND-PORT-9885')}
                  className="text-[10px] text-slate-400 hover:text-slate-200 underline"
                >
                  Fill Port QR
                </button>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-2 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={handleCheckIn}
                disabled={actionLoading || selectedAsg?.status === 'CHECKED_IN' || selectedAsg?.status === 'COMPLETED'}
                className="py-3 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl text-xs font-bold shadow-lg shadow-emerald-600/30 flex items-center justify-center gap-2 transition-all"
              >
                <LogIn className="w-4 h-4" />
                <span>CHECK IN</span>
              </button>

              <button
                type="button"
                onClick={handleCheckOut}
                disabled={actionLoading || selectedAsg?.status !== 'CHECKED_IN'}
                className="py-3 px-4 bg-rose-600 hover:bg-rose-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-xl text-xs font-bold shadow-lg shadow-rose-600/30 flex items-center justify-center gap-2 transition-all"
              >
                <LogOut className="w-4 h-4" />
                <span>CHECK OUT</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
