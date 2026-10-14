import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ShieldCheck, KeyRound, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const MFAVerify = () => {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { verifyMFA } = useAuth();

  const userId = location.state?.userId;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await verifyMFA(userId, code);
      const role = user?.role;
      if (role === 'ADMIN') navigate('/dashboard/admin');
      else if (role === 'SUPERVISOR') navigate('/dashboard/supervisor');
      else if (role === 'AUDITOR') navigate('/dashboard/auditor');
      else navigate('/dashboard/guard');
    } catch (err) {
      setError(err?.message || 'Invalid MFA code. Try standard test code: 123456');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex p-3 bg-purple-600 rounded-2xl text-white shadow-xl shadow-purple-500/20 mb-4">
          <KeyRound className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Two-Factor Authentication</h2>
        <p className="mt-1 text-xs text-slate-400">
          Enter the 6-digit TOTP code from your authenticator app
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-900 border border-slate-800 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-950/80 border border-rose-800 text-rose-300 text-xs">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                Authentication Code
              </label>
              <input
                type="text"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                placeholder="123456"
                className="w-full text-center tracking-[0.5em] text-2xl font-mono bg-slate-950 border border-slate-700 rounded-lg py-3 text-slate-100 focus:outline-none focus:border-purple-500"
                required
                autoFocus
              />
            </div>

            <p className="text-[11px] text-slate-500 text-center">
              💡 Demo bypass: Use <code className="text-purple-400 bg-slate-950 px-1 py-0.5 rounded">123456</code> or generated Google Authenticator TOTP.
            </p>

            <button
              type="submit"
              disabled={loading || code.length < 6}
              className="w-full flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold py-2.5 px-4 rounded-lg shadow-lg shadow-purple-600/30 transition-all disabled:opacity-50"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>Verify TOTP Token</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
