import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  LayoutDashboard,
  Users,
  MapPin,
  Clock,
  CalendarCheck,
  CheckCircle2,
  FileCheck2,
  FileText,
  LogOut,
  Bell,
  Menu,
  X,
  Wifi,
  WifiOff,
  Radio,
  Fingerprint
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { Badge } from '../components/common/Badge';
import api from '../services/api';

export const AppLayout = () => {
  const { user, logout, role, isAdmin, isSupervisor, isAuditor, isGuard } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // Fetch initial notifications
  const fetchNotifications = async () => {
    try {
      const res = await api.get('/notifications?unread_only=false');
      setNotifications(res || []);
      setUnreadCount((res || []).filter((n) => !n.read).length);
    } catch (e) {
      console.error('Error fetching notifications', e);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  // Listen to WebSocket events in real-time
  const { isConnected } = useWebSocket('/ws/notifications', (event) => {
    if (event.event === 'notification') {
      setNotifications((prev) => [event.data, ...prev]);
      setUnreadCount((prev) => prev + 1);
    }
  });

  const markNotificationRead = async (id) => {
    try {
      await api.put(`/notifications/${id}/read`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (e) {
      console.error(e);
    }
  };

  // Nav links based on RBAC
  const navLinks = [
    // Dashboards
    ...(isAdmin ? [{ to: '/dashboard/admin', label: 'Admin Dashboard', icon: LayoutDashboard }] : []),
    ...(isSupervisor ? [{ to: '/dashboard/supervisor', label: 'Supervisor Console', icon: LayoutDashboard }] : []),
    ...(isAuditor ? [{ to: '/dashboard/auditor', label: 'Auditor Overview', icon: LayoutDashboard }] : []),
    ...(isGuard ? [{ to: '/dashboard/guard', label: 'Guard Portal', icon: Radio }] : []),

    // Shared / Role Specific Management
    ...(isAdmin ? [{ to: '/users', label: 'User Management', icon: Users }] : []),
    ...(!isGuard ? [{ to: '/sites', label: 'Sites & Geofences', icon: MapPin }] : []),
    ...(!isGuard ? [{ to: '/shifts', label: 'Shift Schedules', icon: Clock }] : []),
    ...(!isGuard ? [{ to: '/assignments', label: 'Assignments', icon: CalendarCheck }] : []),
    { to: '/attendance', label: 'Attendance Records', icon: CheckCircle2 },
    ...(!isGuard ? [{ to: '/compliance', label: 'Compliance Center', icon: ShieldAlert }] : []),
    ...(isAdmin || isAuditor ? [{ to: '/audit', label: 'Audit Explorer', icon: Fingerprint }] : []),
    ...(!isGuard ? [{ to: '/reports', label: 'Audit Reports', icon: FileText }] : []),
  ];

  return (
    <div className="flex h-screen bg-slate-900 text-slate-100 overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-950 border-r border-slate-800 flex flex-col transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-120 lg:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-600 rounded-lg text-white shadow-lg shadow-blue-500/20">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-tight text-white leading-tight">AEGIS COMPLIANCE</h1>
              <p className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">Security Operations</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {navLinks.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30 font-semibold'
                      : 'text-slate-400 hover:bg-slate-850 hover:text-slate-100'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Card & Logout in Sidebar Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60">
          <div className="flex items-center justify-between">
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-semibold truncate text-slate-200">{user?.name}</span>
              <div className="mt-1 flex items-center gap-1.5">
                <Badge variant={user?.role} label={user?.role} />
              </div>
            </div>
            <button
              onClick={() => {
                logout();
                navigate('/login');
              }}
              title="Sign Out"
              className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-850 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Navbar */}
        <header className="h-16 bg-slate-900/80 border-b border-slate-800 backdrop-blur-md px-6 flex items-center justify-between z-30">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400">
              <span className="text-slate-500 font-mono">NODE: PROD-SEC-US1</span>
              <span>•</span>
              <span>TAMPER-EVIDENT LOGGING: ACTIVE</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Real-time Status Indicator */}
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
                isConnected
                  ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60'
                  : 'bg-amber-950/60 text-amber-400 border-amber-800/60'
              }`}
            >
              {isConnected ? (
                <>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="hidden sm:inline">LIVE SYNC</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3.5 h-3.5 text-amber-400" />
                  <span className="hidden sm:inline">OFFLINE FALLBACK</span>
                </>
              )}
            </div>

            {/* Notification Center */}
            <div className="relative">
              <button
                onClick={() => setNotificationsOpen(!notificationsOpen)}
                className="relative p-2 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 transition-colors"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 bg-rose-500 text-white rounded-full text-[10px] font-bold flex items-center justify-center animate-bounce">
                    {unreadCount}
                  </span>
                )}
              </button>

              {/* Notification Dropdown */}
              {notificationsOpen && (
                <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-50 overflow-hidden">
                  <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                      Operational Alerts
                    </span>
                    <span className="text-xs text-blue-400 font-semibold">{unreadCount} unread</span>
                  </div>
                  <div className="max-h-80 overflow-y-auto divide-y divide-slate-800">
                    {notifications.length === 0 ? (
                      <p className="p-6 text-center text-xs text-slate-500">No recent notifications</p>
                    ) : (
                      notifications.slice(0, 10).map((n) => (
                        <div
                          key={n.id}
                          onClick={() => markNotificationRead(n.id)}
                          className={`p-3 text-xs transition-colors cursor-pointer hover:bg-slate-800/60 ${
                            n.read ? 'opacity-60 bg-transparent' : 'bg-blue-950/20'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <span className="font-semibold text-slate-200">{n.title}</span>
                            <span className="text-[10px] text-slate-500">
                              {n.created_at ? n.created_at.slice(11, 16) : ''}
                            </span>
                          </div>
                          <p className="text-slate-400 mt-1 line-clamp-2">{n.message}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-900">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
