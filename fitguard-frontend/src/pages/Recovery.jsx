import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip
} from 'recharts';
import { Moon, Droplets, BedDouble } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';

const Recovery = () => {
  const { user } = useAuth();
  const [recoveryForm, setRecoveryForm] = useState({
    date: new Date().toISOString().split('T')[0],
    sleep_hrs: '',
    rest_days: 0
  });
  const [hydrationForm, setHydrationForm] = useState({
    date: new Date().toISOString().split('T')[0],
    liters: ''
  });
  const [trend, setTrend] = useState([]);
  const [restTracker, setRestTracker] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    if (!user?.id) return;
    const [trendRes, restRes] = await Promise.all([
      api.get(`/recovery/score-trend/${user.id}`),
      api.get(`/recovery/rest-days/${user.id}`)
    ]);
    setTrend(trendRes.data.trend || []);
    setRestTracker(restRes.data || null);
  };

  useEffect(() => {
    const run = async () => {
      try {
        await loadData();
      } catch (error) {
        console.error('Failed to load recovery data', error);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [user?.id]);

  const logRecovery = async (event) => {
    event.preventDefault();
    try {
      await api.post('/recovery/log', {
        ...recoveryForm,
        sleep_hrs: parseFloat(recoveryForm.sleep_hrs),
        rest_days: parseInt(recoveryForm.rest_days, 10)
      });
      await loadData();
      setRecoveryForm((previous) => ({ ...previous, sleep_hrs: '' }));
    } catch (error) {
      console.error('Failed to log recovery', error);
    }
  };

  const logHydration = async (event) => {
    event.preventDefault();
    try {
      await api.post('/recovery/hydration/log', {
        ...hydrationForm,
        liters: parseFloat(hydrationForm.liters)
      });
      await loadData();
      setHydrationForm((previous) => ({ ...previous, liters: '' }));
    } catch (error) {
      console.error('Failed to log hydration', error);
    }
  };

  if (loading) {
    return <div className="animate-pulse h-64 rounded-2xl bg-slate-200" />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Recovery & Wellness</h1>
        <p className="text-slate-500 mt-1">Track sleep, hydration, rest days, and recovery score trends.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Moon size={18} className="text-indigo-500" /> Sleep & Rest Logging
          </h2>
          <form onSubmit={logRecovery} className="space-y-4">
            <input
              type="date"
              className="w-full rounded-xl border border-slate-300 px-3 py-2"
              value={recoveryForm.date}
              onChange={(e) => setRecoveryForm((prev) => ({ ...prev, date: e.target.value }))}
              required
            />
            <input
              type="number"
              min="1"
              max="12"
              step="0.1"
              className="w-full rounded-xl border border-slate-300 px-3 py-2"
              placeholder="Sleep hours"
              value={recoveryForm.sleep_hrs}
              onChange={(e) => setRecoveryForm((prev) => ({ ...prev, sleep_hrs: e.target.value }))}
              required
            />
            <input
              type="number"
              min="0"
              max="7"
              className="w-full rounded-xl border border-slate-300 px-3 py-2"
              placeholder="Rest days this week"
              value={recoveryForm.rest_days}
              onChange={(e) => setRecoveryForm((prev) => ({ ...prev, rest_days: e.target.value }))}
              required
            />
            <button className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white py-2.5 font-medium">
              Save Recovery Entry
            </button>
          </form>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Droplets size={18} className="text-cyan-500" /> Hydration Logging
          </h2>
          <form onSubmit={logHydration} className="space-y-4">
            <input
              type="date"
              className="w-full rounded-xl border border-slate-300 px-3 py-2"
              value={hydrationForm.date}
              onChange={(e) => setHydrationForm((prev) => ({ ...prev, date: e.target.value }))}
              required
            />
            <input
              type="number"
              min="0.1"
              max="10"
              step="0.1"
              className="w-full rounded-xl border border-slate-300 px-3 py-2"
              placeholder="Liters"
              value={hydrationForm.liters}
              onChange={(e) => setHydrationForm((prev) => ({ ...prev, liters: e.target.value }))}
              required
            />
            <button className="w-full rounded-xl bg-cyan-600 hover:bg-cyan-700 text-white py-2.5 font-medium">
              Save Hydration
            </button>
          </form>
          <div className="mt-6 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
            <p className="flex items-center gap-2">
              <BedDouble size={16} className="text-slate-500" />
              Rest days in last {restTracker?.window_days || 14} days: {restTracker?.rest_days || 0}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-5">
        <h2 className="font-semibold text-slate-800 mb-4">Recovery Score Trend</h2>
        <div className="h-72">
          {trend.length ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} />
                <RechartsTooltip />
                <Line dataKey="score" stroke="#10b981" strokeWidth={3} />
                <Line dataKey="sleep_hrs" stroke="#6366f1" strokeWidth={2} />
                <Line dataKey="hydration_liters" stroke="#06b6d4" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-400">No recovery logs yet.</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Recovery;

