import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip
} from 'recharts';
import { Activity, AlertTriangle, Brain, CalendarDays, TrendingUp } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';

const StatCard = ({ title, value, subtitle, icon, tone = 'slate' }) => (
  <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm text-slate-500">{title}</p>
        <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
        <p className="text-xs text-slate-500 mt-2">{subtitle}</p>
      </div>
      <div className={`p-3 rounded-xl ${tone === 'red' ? 'bg-red-100 text-red-600' : tone === 'amber' ? 'bg-amber-100 text-amber-600' : tone === 'blue' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-600'}`}>
        {icon}
      </div>
    </div>
  </div>
);

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [dashboard, setDashboard] = useState(null);
  const [restSuggestion, setRestSuggestion] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      if (!user?.id) return;
      try {
        const [dashboardRes, restRes] = await Promise.all([
          api.get(`/analytics/dashboard/${user.id}`),
          api.get(`/planning/recommend-rest-day/${user.id}`).catch(() => ({ data: null }))
        ]);
        setDashboard(dashboardRes.data);
        setRestSuggestion(restRes?.data || null);
      } catch (error) {
        console.error('Failed to load dashboard', error);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [user?.id]);

  const latestRisk = useMemo(() => {
    if (!dashboard?.injury_risk_progression?.length) return null;
    return dashboard.injury_risk_progression[dashboard.injury_risk_progression.length - 1];
  }, [dashboard]);

  const latestFatigue = dashboard?.fatigue?.latest;
  const weeklySummary = dashboard?.weekly_summary || {};
  const unreadAlerts = (dashboard?.alerts || []).filter((alert) => !alert.is_read);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-500 mt-1">Welcome back, {user?.name?.split(' ')[0] || 'Athlete'}.</p>
      </div>

      {unreadAlerts.some((a) => a.alert_type === 'high_risk_banner') && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 flex items-center gap-3">
          <AlertTriangle className="text-red-600" />
          <p className="text-red-700 font-medium">
            High injury risk detected. Reduce intensity and prioritize recovery.
          </p>
        </div>
      )}

      {unreadAlerts.some((a) => a.alert_type === 'pre_session_fatigue_warning') && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-700">
          Pre-session warning: your fatigue is currently high.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Weekly Hours"
          value={`${weeklySummary.total_hours || 0}h`}
          subtitle={`${weeklySummary.sessions || 0} sessions`}
          icon={<Activity size={20} />}
          tone="blue"
        />
        <StatCard
          title="Avg Intensity"
          value={`${weeklySummary.avg_intensity || 0}/10`}
          subtitle="Last 7 days"
          icon={<TrendingUp size={20} />}
          tone="amber"
        />
        <StatCard
          title="Current Fatigue"
          value={latestFatigue ? `${latestFatigue.score}` : '--'}
          subtitle={latestFatigue?.level_label || 'No data'}
          icon={<Brain size={20} />}
          tone={latestFatigue?.level === 2 ? 'red' : latestFatigue?.level === 1 ? 'amber' : 'slate'}
        />
        <StatCard
          title="Injury Risk"
          value={latestRisk ? `${latestRisk.risk_score}%` : '--'}
          subtitle={latestRisk?.risk_level || 'No prediction'}
          icon={<AlertTriangle size={20} />}
          tone={latestRisk?.risk_level === 'High' ? 'red' : latestRisk?.risk_level === 'Medium' ? 'amber' : 'slate'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-5">
          <h2 className="font-semibold text-slate-800 mb-4">Weekly Training Load Trend</h2>
          <div className="h-72">
            {dashboard?.training_load_trends?.weekly?.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dashboard.training_load_trends.weekly}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="week_start" tick={{ fontSize: 12 }} />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="training_load" stroke="#0284c7" strokeWidth={3} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400">No training data yet.</div>
            )}
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5 space-y-4">
          <div>
            <h2 className="font-semibold text-slate-800">Weekly Summary</h2>
            <p className="text-sm text-slate-500 mt-1">
              Risk trend: <span className="font-medium uppercase">{weeklySummary.risk_trend || 'stable'}</span>
            </p>
          </div>
          <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
            {restSuggestion?.recommended_rest_day ? (
              <p>
                Recommended rest day: <span className="font-semibold">{restSuggestion.recommended_rest_day}</span>
              </p>
            ) : (
              <p>No rest-day recommendation available yet.</p>
            )}
          </div>
          <button
            onClick={() => navigate('/planning')}
            className="w-full rounded-xl bg-primary-600 hover:bg-primary-700 text-white py-3 font-medium"
          >
            Open Weekly Planner
          </button>
          <button
            onClick={() => navigate('/log-training')}
            className="w-full rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 py-3 font-medium"
          >
            Log Training Session
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-5">
        <h2 className="font-semibold text-slate-800 mb-4">Alerts & Reminders</h2>
        {dashboard?.alerts?.length ? (
          <div className="space-y-3">
            {dashboard.alerts.slice(0, 6).map((alert) => (
              <div key={alert.id} className="rounded-xl border border-slate-200 p-3 flex items-start gap-3">
                <CalendarDays size={18} className="text-slate-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-slate-800">{alert.message}</p>
                  <p className="text-xs text-slate-500 mt-1">{new Date(alert.created_at).toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400">No alerts right now.</p>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
