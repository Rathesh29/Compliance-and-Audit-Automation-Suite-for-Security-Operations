import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          const profile = await api.get('/auth/me');
          setUser(profile);
        } catch (err) {
          console.error('Failed to restore session', err);
          logout();
        }
      }
      setLoading(false);
    };
    initializeAuth();
  }, []);

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    if (response.mfa_required) {
      return { mfa_required: true, user_id: response.user_id };
    }

    localStorage.setItem('token', response.access_token);
    setToken(response.access_token);

    const profile = await api.get('/auth/me');
    setUser(profile);
    return { mfa_required: false, user: profile };
  };

  const verifyMFA = async (userId, code) => {
    const response = await api.post('/auth/mfa', { user_id: userId, code });
    localStorage.setItem('token', response.access_token);
    setToken(response.access_token);

    const profile = await api.get('/auth/me');
    setUser(profile);
    return profile;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const role = user?.role || '';
  const isAdmin = role === 'ADMIN';
  const isSupervisor = role === 'SUPERVISOR';
  const isAuditor = role === 'AUDITOR';
  const isGuard = role === 'GUARD';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: !!token && !!user,
        login,
        verifyMFA,
        logout,
        isAdmin,
        isSupervisor,
        isAuditor,
        isGuard,
        role
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
