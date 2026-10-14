import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AppLayout } from '../layouts/AppLayout';
import { Login } from '../pages/Login';
import { MFAVerify } from '../pages/MFAVerify';
import { AdminDashboard } from '../pages/AdminDashboard';
import { SupervisorDashboard } from '../pages/SupervisorDashboard';
import { AuditorDashboard } from '../pages/AuditorDashboard';
import { GuardDashboard } from '../pages/GuardDashboard';
import { UsersPage } from '../pages/UsersPage';
import { SitesPage } from '../pages/SitesPage';
import { ShiftsPage } from '../pages/ShiftsPage';
import { AssignmentsPage } from '../pages/AssignmentsPage';
import { AttendancePage } from '../pages/AttendancePage';
import { CompliancePage } from '../pages/CompliancePage';
import { AuditPage } from '../pages/AuditPage';
import { ReportsPage } from '../pages/ReportsPage';

const ProtectedRoute = ({ children, allowedRoles }) => {
  const { isAuthenticated, loading, role } = useAuth();

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-slate-950">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(role)) {
    // Redirect to user's permitted home
    if (role === 'GUARD') return <Navigate to="/dashboard/guard" replace />;
    if (role === 'AUDITOR') return <Navigate to="/dashboard/auditor" replace />;
    if (role === 'SUPERVISOR') return <Navigate to="/dashboard/supervisor" replace />;
    return <Navigate to="/dashboard/admin" replace />;
  }

  return children;
};

const RoleRedirect = () => {
  const { role, isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (role === 'ADMIN') return <Navigate to="/dashboard/admin" replace />;
  if (role === 'SUPERVISOR') return <Navigate to="/dashboard/supervisor" replace />;
  if (role === 'AUDITOR') return <Navigate to="/dashboard/auditor" replace />;
  return <Navigate to="/dashboard/guard" replace />;
};

export const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/mfa" element={<MFAVerify />} />

      {/* Authenticated Application */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<RoleRedirect />} />

        {/* Role Dashboards */}
        <Route
          path="/dashboard/admin"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/supervisor"
          element={
            <ProtectedRoute allowedRoles={['SUPERVISOR', 'ADMIN']}>
              <SupervisorDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/auditor"
          element={
            <ProtectedRoute allowedRoles={['AUDITOR', 'ADMIN']}>
              <AuditorDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/dashboard/guard"
          element={
            <ProtectedRoute allowedRoles={['GUARD', 'ADMIN', 'SUPERVISOR']}>
              <GuardDashboard />
            </ProtectedRoute>
          }
        />

        {/* Management Routes */}
        <Route
          path="/users"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <UsersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/sites"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR', 'AUDITOR']}>
              <SitesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/shifts"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR', 'AUDITOR']}>
              <ShiftsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/assignments"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR', 'AUDITOR']}>
              <AssignmentsPage />
            </ProtectedRoute>
          }
        />
        <Route path="/attendance" element={<AttendancePage />} />
        <Route
          path="/compliance"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR', 'AUDITOR']}>
              <CompliancePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/audit"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'AUDITOR']}>
              <AuditPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports"
          element={
            <ProtectedRoute allowedRoles={['ADMIN', 'SUPERVISOR', 'AUDITOR']}>
              <ReportsPage />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
