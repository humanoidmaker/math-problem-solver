import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Calculator, Dumbbell, History, LayoutDashboard, LogOut } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  user: { name: string; email: string } | null;
  onLogout: () => void;
}

const navItems = [
  { path: '/', label: 'Solve', icon: Calculator },
  { path: '/practice', label: 'Practice', icon: Dumbbell },
  { path: '/history', label: 'History', icon: History },
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
];

export default function Layout({ children, user, onLogout }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-64 bg-primary-500 text-white flex flex-col fixed h-full">
        <div className="p-6 border-b border-primary-400">
          <h1 className="text-xl font-bold">MathLens</h1>
          <p className="text-gray-400 text-sm mt-1">Math Problem Solver</p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                location.pathname === path
                  ? 'bg-accent-500 text-white'
                  : 'text-gray-300 hover:bg-primary-400'
              }`}
            >
              <Icon size={20} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-primary-400">
          <div className="text-sm text-gray-400 mb-2">{user?.name}</div>
          <button
            onClick={onLogout}
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors text-sm"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      </aside>
      <main className="ml-64 flex-1 p-8">{children}</main>
    </div>
  );
}
