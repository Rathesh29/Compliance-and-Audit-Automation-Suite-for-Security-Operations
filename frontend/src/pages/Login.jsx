import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, Lock, Mail, ArrowRight, ShieldCheck, UserCheck } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Login = () => {
  const [email, setEmail] = useState('admin@security-ops.com');
  const [password, setPassword] = useState('Password123!');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(email, password);
      if (result.mfa_required) {
        navigate('/mfa', { state: { userId: result.user_id } });
      } else {
        const role = result.user?.role;
        if (role === 'ADMIN') navigate('/dashboard/admin');
        else if (role === 'SUPERVISOR') navigate('/dashboard/supervisor');
        else if (role === 'AUDITOR') navigate('/dashboard/auditor');
        else navigate('/dashboard/guard');
      }
    } catch (err) {
      setError(err?.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const setDemoAccount = (demoEmail) => {
    setEmail(demoEmail);
    setPassword('Password123!');
    setError('');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-blue-600/10 blur-[120px] pointer-events-none rounded-full" />
      <div className="absolute bottom-0 right-10 w-[500px] h-[300px] bg-indigo-600/10 blur-[100px] pointer-events-none rounded-full" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center z-10">
        <div className="inline-flex p-3 bg-blue-600 rounded-2xl text-white shadow-xl shadow-blue-500/20 mb-4 border border-blue-400/30">
          <ShieldAlert className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-black text-white tracking-tight">
          SECURITY COMPLIANCE & AUDIT SUITE
        </h2>
        <p className="mt-1.5 text-xs uppercase tracking-widest text-slate-400 font-semibold">
          Operations Verification Gateway
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10">
        <div className="bg-slate-900 border border-slate-800 py-8 px-6 shadow-2xl rounded-2xl sm:px-10 backdrop-blur-md">
          {error && (
            <div className="mb-5 p-3 rounded-xl bg-rose-950/80 border border-rose-800/80 text-rose-300 text-xs flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="name@security-ops.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                  placeholder="••••••••••••"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold py-2.5 px-4 rounded-lg shadow-lg shadow-blue-600/30 transition-all disabled:opacity-50"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Authenticate Session</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Credentials Auto-Fill */}
          <div className="mt-6 pt-5 border-t border-slate-800">
            <p className="text-[11px] uppercase font-semibold text-slate-400 mb-2.5 text-center">
              Quick Role Switch 
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => setDemoAccount('admin@security-ops.com')}
                className="py-1.5 px-2 bg-slate-950 border border-slate-800 hover:border-purple-500 rounded-lg text-slate-300 hover:text-purple-300 transition-colors text-left"
              >
                👑 <b>Admin</b>
              </button>
              <button
                type="button"
                onClick={() => setDemoAccount('supervisor.jenkins@security-ops.com')}
                className="py-1.5 px-2 bg-slate-950 border border-slate-800 hover:border-cyan-500 rounded-lg text-slate-300 hover:text-cyan-300 transition-colors text-left"
              >
                👮 <b>Supervisor</b>
              </button>
              <button
                type="button"
                onClick={() => setDemoAccount('auditor.rostova@security-ops.com')}
                className="py-1.5 px-2 bg-slate-950 border border-slate-800 hover:border-amber-500 rounded-lg text-slate-300 hover:text-amber-300 transition-colors text-left"
              >
                🔍 <b>Auditor</b>
              </button>
              <button
                type="button"
                onClick={() => setDemoAccount('guard.001@security-ops.com')}
                className="py-1.5 px-2 bg-slate-950 border border-slate-800 hover:border-blue-500 rounded-lg text-slate-300 hover:text-blue-300 transition-colors text-left"
              >
                🛡️ <b>Guard 001</b>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
