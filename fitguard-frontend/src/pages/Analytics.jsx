import React, { useEffect, useMemo, useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  Legend
} from 'recharts';
import { Brain, Gauge, HeartPulse, RefreshCcw, TrendingUp } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';
import PlotlyFatigueGauge from '../components/PlotlyFatigueGauge';

const zoneColors = ['#16a34a', '#f59e0b', '#f97316', '#ef4444'];

const CalendarHeatmap = ({ data }) => {
  const map = useMemo(() => {
    const keyed = new Map();
    (data || []).forEach((entry) => keyed.set(entry.date, entry.training_load));
    return keyed;
  }, [data]);

  const days = [];
  const today = new Date();
  for (let i = 83; i >= 0; i -= 1) {
    const day = new Date(today);
    day.setDate(today.getDate() - i);
    days.push(day);
  }

  const values = Array.from(map.values());
  const max = values.length ? Math.max(...values) : 1;

  const colorFor = (value) => {
    if (!value) return 'bg-slate-100';
    const ratio = value / max;
    if (ratio >= 0.75) return 'bg-primary-700';
    if (ratio >= 0.5) return 'bg-primary-500';
    if (ratio >= 0.25) return 'bg-primary-300';
    return 'bg-primary-100';
  };

  return (
    <div>
      <div className="grid grid-cols-12 gap-1">
        {days.map((day) => {
          const key = day.toISOString().split('T')[0];
          const value = map.get(key) || 0;
          return (
            <div
              key={key}
              title={`${key}: load ${value.toFixed(2)}`}
              className={`w-full h-4 rounded-sm ${colorFor(value)}`}
            />
          );
        })}
      </div>
      <p className="text-xs text-slate-500 mt-2">Distance & duration heatmap (last 12 weeks)</p>
    </div>
  );
};

const MetricCard = ({ label, value, helper }) => (
  <div className="bg-white border border-slate-200 rounded-2xl p-4">
    <p className="text-sm text-slate-500">{label}</p>
    <p className="text-2xl font-bold text-slate-900 mt-1">{value}</p>
    {helper && <p className="text-xs text-slate-500 mt-2">{helper}</p>}
  </div>
);

const Analytics = () => {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [modelStats, setModelStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetraining, setIsRetraining] = useState(false);

  const fetchData = async () => {
    if (!user?.id) return;
    const [dashboardRes, modelRes] = await Promise.all([
      api.get(`/analytics/dashboard/${user.id}`),
      api.get('/predict/model/metrics')
    ]);
    setDashboard(dashboardRes.data);
    setModelStats(modelRes.data);
  };

  useEffect(() => {
    const load = async () => {
      try {
        await fetchData();
      } catch (error) {
        console.error('Failed to load analytics', error);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [user?.id]);

  const retrainModel = async () => {
    setIsRetraining(true);
    try {
      await api.post('/predict/model/retrain', {});
      await fetchData();
    } catch (error) {
      console.error('Failed to retrain model', error);
    } finally {
      setIsRetraining(false);
    }
  };

  if (isLoading) {
    return <div className="animate-pulse bg-slate-200 rounded-2xl h-64" />;
  }

  const weeklyLoad = dashboard?.training_load_trends?.weekly || [];
  const monthlyLoad = dashboard?.training_load_trends?.monthly || [];
  const fatigueHistory = dashboard?.fatigue?.history || [];
  const currentFatigue = dashboard?.fatigue?.latest?.score || 0;
  const riskProgression = dashboard?.injury_risk_progression || [];
  const hrZones = dashboard?.heart_rate_zones?.breakdown || [];
  const balance = dashboard?.recovery_training_balance || [];
  const heatmap = dashboard?.heatmap_calendar || [];
  const advanced = dashboard?.advanced_metrics || {};
  const scatter = advanced.risk_performance_scatter || [];
  const modelMetrics = modelStats?.dashboard?.metrics || {};
  const featureImportance = modelStats?.feature_importance_ranked || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-2">
            <TrendingUp className="text-primary-600" /> Analytics & Visualization
          </h1>
          <p className="text-slate-500 mt-1">Training load, fatigue, injury risk, recovery, and ML diagnostics.</p>
        </div>
        <button
          onClick={retrainModel}
          disabled={isRetraining}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white px-4 py-2.5 disabled:opacity-60"
        >
          <RefreshCcw size={16} className={isRetraining ? 'animate-spin' : ''} />
          {isRetraining ? 'Retraining Model...' : 'Retrain Model'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard label="ACWR" value={advanced.acwr ?? 0} helper="Acute:Chronic workload ratio" />
        <MetricCard label="Monotony" value={advanced.monotony ?? 0} helper="Weekly load mean / std deviation" />
        <MetricCard label="Strain" value={advanced.strain ?? 0} helper="Weekly load x monotony" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h2 className="font-semibold text-slate-800 mb-4">Training Load Trends</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={weeklyLoad}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="week_start" tick={{ fontSize: 12 }} />
                <YAxis />
                <RechartsTooltip />
                <Line type="monotone" dataKey="training_load" stroke="#0284c7" strokeWidth={3} name="Weekly load" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="h-44 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyLoad}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="training_load" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Gauge size={18} className="text-primary-600" /> Fatigue Level Gauge (Plotly)
          </h2>
          <PlotlyFatigueGauge value={currentFatigue} title="Current Fatigue" />
          <div className="h-44 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={fatigueHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} />
                <RechartsTooltip />
                <Line type="monotone" dataKey="score" stroke="#8b5cf6" strokeWidth={2.5} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Brain size={18} className="text-orange-500" /> Injury Risk Progression
          </h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={riskProgression}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 100]} />
                <RechartsTooltip />
                <Area type="monotone" dataKey="confidence_upper" fill="#fed7aa" stroke="#fdba74" name="CI upper" />
                <Area type="monotone" dataKey="confidence_lower" fill="#fff7ed" stroke="#fdba74" name="CI lower" />
                <Line type="monotone" dataKey="risk_score" stroke="#f97316" strokeWidth={3} name="Risk %" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <HeartPulse size={18} className="text-red-500" /> Heart Rate Zone Breakdown
          </h2>
          <div className="h-72">
            {hrZones.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={hrZones} dataKey="hours" nameKey="zone" outerRadius={90} label>
                    {hrZones.map((entry, idx) => (
                      <Cell key={entry.zone} fill={zoneColors[idx % zoneColors.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400">No heart-rate logs available.</div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h2 className="font-semibold text-slate-800 mb-4">Recovery vs Training Balance</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={balance}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" domain={[0, 100]} />
                <RechartsTooltip />
                <Line yAxisId="left" type="monotone" dataKey="training_load" stroke="#0284c7" strokeWidth={2.5} name="Training load" />
                <Line yAxisId="right" type="monotone" dataKey="recovery_score" stroke="#10b981" strokeWidth={2.5} name="Recovery score" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h2 className="font-semibold text-slate-800 mb-4">Distance & Duration Heatmap Calendar</h2>
          <CalendarHeatmap data={heatmap} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h2 className="font-semibold text-slate-800 mb-4">Risk vs Performance Correlation</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="performance_score" name="Performance" />
                <YAxis dataKey="risk_score" name="Risk %" />
                <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} />
                <Scatter data={scatter} fill="#0ea5e9" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h2 className="font-semibold text-slate-800 mb-4">Model Accuracy Dashboard</h2>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <MetricCard label="Precision" value={modelMetrics.precision ?? 0} />
            <MetricCard label="Recall" value={modelMetrics.recall ?? 0} />
            <MetricCard label="F1 Score" value={modelMetrics.f1_score ?? 0} />
            <MetricCard label="Accuracy" value={modelMetrics.accuracy ?? 0} />
          </div>
          <p className="text-sm text-slate-500 mb-3">Feature importance (Random Forest):</p>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={featureImportance}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="feature" tick={{ fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={62} />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="importance" fill="#334155" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;

