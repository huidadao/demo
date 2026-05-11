'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use_auth';
import { authApi } from '@/lib/api';
import toast from 'react-hot-toast';

interface UserStatus {
  id: number;
  email: string;
  status: 'online' | 'away' | 'offline';
  last_seen: string | null;
  created_at: string | null;
}

interface DashboardStats {
  total_users: number;
  today_signups: number;
  active_users: number;
  users: UserStatus[];
}

function getInitials(email: string) {
  return email?.split('@')[0].slice(0, 2).toUpperCase() || 'U';
}

function formatLastSeen(isoString: string | null) {
  if (!isoString) return 'Never';
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  return date.toLocaleDateString();
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // Fetch dashboard stats
  const fetchStats = async () => {
    try {
      const data = await authApi.getStats();
      setStats(data);
    } catch {
      // silent fail on polling
    } finally {
      setStatsLoading(false);
    }
  };

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Polling stats every 10 seconds
  useEffect(() => {
    if (!isAuthenticated) return;
    fetchStats();
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, [isAuthenticated]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    router.push('/login');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const initials = getInitials(user?.email || '');

  const onlineUsers = stats?.users.filter((u) => u.status === 'online') || [];
  const awayUsers = stats?.users.filter((u) => u.status === 'away') || [];
  const offlineUsers = stats?.users.filter((u) => u.status === 'offline') || [];

  const statusConfig = {
    online: { label: 'Online', bg: 'bg-green-50', border: 'border-green-200', headerBg: 'bg-green-100', dot: 'bg-green-500', text: 'text-green-700' },
    away: { label: 'Away', bg: 'bg-yellow-50', border: 'border-yellow-200', headerBg: 'bg-yellow-100', dot: 'bg-yellow-500', text: 'text-yellow-700' },
    offline: { label: 'Offline', bg: 'bg-gray-50', border: 'border-gray-200', headerBg: 'bg-gray-100', dot: 'bg-gray-400', text: 'text-gray-600' },
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navbar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Admin Dashboard</h1>
            </div>
            <div className="flex items-center" ref={dropdownRef}>
              <div className="relative">
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <span className="text-sm text-white font-medium">{initials}</span>
                  </div>
                  <span className="text-sm text-gray-700 hidden sm:inline">{user?.email}</span>
                  <svg
                    className={`w-4 h-4 text-gray-500 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {isDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                    <div className="px-4 py-3 border-b border-gray-100">
                      <p className="text-sm font-medium text-gray-900">{user?.email}</p>
                      <p className="text-xs text-gray-500">Account</p>
                    </div>
                    <button
                      onClick={() => { setIsDropdownOpen(false); router.push('/profile'); }}
                      className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                      Profile
                    </button>
                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Total Users</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {statsLoading ? '-' : stats?.total_users ?? 0}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Today's Signups</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {statsLoading ? '-' : stats?.today_signups ?? 0}
                </p>
              </div>
              <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500">Active Now</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {statsLoading ? '-' : stats?.active_users ?? 0}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Kanban Board */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Online Column */}
          <div className={`rounded-xl border ${statusConfig.online.border} ${statusConfig.bg}`}>
            <div className={`px-4 py-3 ${statusConfig.online.headerBg} rounded-t-xl border-b ${statusConfig.online.border} flex items-center justify-between`}>
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${statusConfig.online.dot}`}></span>
                <h3 className={`font-semibold ${statusConfig.online.text}`}>Online</h3>
              </div>
              <span className={`text-xs font-bold px-2 py-1 rounded-full bg-white ${statusConfig.online.text}`}>
                {onlineUsers.length}
              </span>
            </div>
            <div className="p-3 space-y-3 min-h-[200px]">
              {onlineUsers.length === 0 && (
                <div className="text-center py-8 text-sm text-gray-400">No users online</div>
              )}
              {onlineUsers.map((u) => (
                <div key={u.id} className="bg-white rounded-lg p-3 shadow-sm border border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-green-100 text-green-700 rounded-full flex items-center justify-center text-xs font-bold">
                      {getInitials(u.email)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{u.email}</p>
                      <p className="text-xs text-gray-500">{formatLastSeen(u.last_seen)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Away Column */}
          <div className={`rounded-xl border ${statusConfig.away.border} ${statusConfig.bg}`}>
            <div className={`px-4 py-3 ${statusConfig.away.headerBg} rounded-t-xl border-b ${statusConfig.away.border} flex items-center justify-between`}>
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${statusConfig.away.dot}`}></span>
                <h3 className={`font-semibold ${statusConfig.away.text}`}>Away</h3>
              </div>
              <span className={`text-xs font-bold px-2 py-1 rounded-full bg-white ${statusConfig.away.text}`}>
                {awayUsers.length}
              </span>
            </div>
            <div className="p-3 space-y-3 min-h-[200px]">
              {awayUsers.length === 0 && (
                <div className="text-center py-8 text-sm text-gray-400">No users away</div>
              )}
              {awayUsers.map((u) => (
                <div key={u.id} className="bg-white rounded-lg p-3 shadow-sm border border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-yellow-100 text-yellow-700 rounded-full flex items-center justify-center text-xs font-bold">
                      {getInitials(u.email)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{u.email}</p>
                      <p className="text-xs text-gray-500">{formatLastSeen(u.last_seen)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Offline Column */}
          <div className={`rounded-xl border ${statusConfig.offline.border} ${statusConfig.bg}`}>
            <div className={`px-4 py-3 ${statusConfig.offline.headerBg} rounded-t-xl border-b ${statusConfig.offline.border} flex items-center justify-between`}>
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${statusConfig.offline.dot}`}></span>
                <h3 className={`font-semibold ${statusConfig.offline.text}`}>Offline</h3>
              </div>
              <span className={`text-xs font-bold px-2 py-1 rounded-full bg-white ${statusConfig.offline.text}`}>
                {offlineUsers.length}
              </span>
            </div>
            <div className="p-3 space-y-3 min-h-[200px]">
              {offlineUsers.length === 0 && (
                <div className="text-center py-8 text-sm text-gray-400">No users offline</div>
              )}
              {offlineUsers.map((u) => (
                <div key={u.id} className="bg-white rounded-lg p-3 shadow-sm border border-gray-100">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-gray-100 text-gray-600 rounded-full flex items-center justify-center text-xs font-bold">
                      {getInitials(u.email)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{u.email}</p>
                      <p className="text-xs text-gray-500">{formatLastSeen(u.last_seen)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
