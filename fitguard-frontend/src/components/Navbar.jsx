import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Activity,
  Brain,
  CalendarDays,
  LayoutDashboard,
  LineChart,
  LogOut,
  Shield,
  UserCircle
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const NavLink = ({ to, icon: Icon, label, isActive }) => (
  <Link
    to={to}
    className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
      isActive ? 'bg-primary-100 text-primary-700 font-medium' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
    }`}
  >
    <Icon size={16} />
    {label}
  </Link>
);

const Navbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const links = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/log-training', icon: Activity, label: 'Log' },
    { to: '/recovery', icon: CalendarDays, label: 'Recovery' },
    { to: '/analytics', icon: LineChart, label: 'Analytics' },
    { to: '/planning', icon: CalendarDays, label: 'Planning' },
    { to: '/coach', icon: Brain, label: 'Smart Coach' },
    { to: '/profile', icon: UserCircle, label: 'Profile' },
    { to: '/coach-admin', icon: Shield, label: 'Coach View' }
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="h-16 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-primary-700 text-white font-bold flex items-center justify-center">
              F
            </div>
            <span className="text-lg font-bold text-slate-800">FitGuard</span>
          </Link>

          {user && (
            <div className="hidden lg:flex items-center gap-1 overflow-x-auto">
              {links.map((link) => (
                  <NavLink
                    key={link.to}
                    to={link.to}
                    icon={link.icon}
                    label={link.label}
                    isActive={location.pathname === link.to}
                  />
                ))}
            </div>
          )}

          <div className="flex items-center gap-3">
            {user ? (
              <>
                <span className="hidden sm:inline text-sm text-slate-600">{user.name}</span>
                <button onClick={handleLogout} className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-red-500">
                  <LogOut size={18} />
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm text-slate-600 hover:text-primary-700">Login</Link>
                <Link to="/register" className="text-sm rounded-lg bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5">
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
      {user && (
        <div className="lg:hidden border-t border-slate-200 px-3 py-2 flex items-center gap-1 overflow-x-auto">
          {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                icon={link.icon}
                label={link.label}
                isActive={location.pathname === link.to}
              />
            ))}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
