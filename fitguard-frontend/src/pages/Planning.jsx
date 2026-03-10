import React, { useEffect, useMemo, useState } from 'react';
import { CalendarDays, Sparkles, Target } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';

const dayLabel = (dateText) =>
  new Date(dateText).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });

const mondayOfCurrentWeek = () => {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - ((day + 6) % 7);
  const monday = new Date(now.setDate(diff));
  return monday.toISOString().split('T')[0];
};

const Planning = () => {
  const { user } = useAuth();
  const [weekStart, setWeekStart] = useState(mondayOfCurrentWeek());
  const [goals, setGoals] = useState([]);
  const [plan, setPlan] = useState([]);
  const [restSuggestion, setRestSuggestion] = useState(null);
  const [goalForm, setGoalForm] = useState({
    goal_type: '',
    target_value: '',
    target_sessions_per_week: '',
    end_date: '',
    notes: ''
  });
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const loadData = async () => {
    if (!user?.id) return;
    const [goalsRes, planRes, restRes] = await Promise.all([
      api.get('/planning/goals'),
      api.get(`/planning/week/${user.id}`, { params: { week_start: weekStart } }),
      api.get(`/planning/recommend-rest-day/${user.id}`).catch(() => ({ data: null }))
    ]);
    setGoals(goalsRes.data || []);
    setPlan(planRes.data?.sessions || []);
    setRestSuggestion(restRes?.data || null);
  };

  useEffect(() => {
    const run = async () => {
      try {
        await loadData();
      } catch (error) {
        console.error('Failed to load planning data', error);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [user?.id, weekStart]);

  const submitGoal = async (event) => {
    event.preventDefault();
    try {
      await api.post('/planning/goals', {
        ...goalForm,
        target_value: goalForm.target_value ? parseFloat(goalForm.target_value) : null,
        target_sessions_per_week: goalForm.target_sessions_per_week ? parseInt(goalForm.target_sessions_per_week, 10) : null
      });
      setGoalForm({ goal_type: '', target_value: '', target_sessions_per_week: '', end_date: '', notes: '' });
      await loadData();
    } catch (error) {
      console.error('Failed to create goal', error);
    }
  };

  const generatePlan = async (useClaude) => {
    setGenerating(true);
    try {
      await api.post('/planning/generate-weekly', { week_start: weekStart, use_claude: useClaude });
      await loadData();
    } catch (error) {
      console.error('Failed to generate plan', error);
    } finally {
      setGenerating(false);
    }
  };

  const planByDate = useMemo(() => {
    const map = new Map();
    (plan || []).forEach((session) => map.set(session.plan_date, session));
    return map;
  }, [plan]);

  const weekDays = useMemo(() => {
    const start = new Date(weekStart);
    const days = [];
    for (let i = 0; i < 7; i += 1) {
      const day = new Date(start);
      day.setDate(start.getDate() + i);
      days.push(day.toISOString().split('T')[0]);
    }
    return days;
  }, [weekStart]);

  if (loading) {
    return <div className="animate-pulse h-64 rounded-2xl bg-slate-200" />;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Planning Features</h1>
          <p className="text-slate-500 mt-1">Weekly training plan, rest-day recommendation, and goal setting.</p>
        </div>
        <div className="flex gap-2">
          <button
            disabled={generating}
            onClick={() => generatePlan(false)}
            className="rounded-xl border border-slate-300 px-4 py-2 hover:bg-slate-50"
          >
            Generate Rule Plan
          </button>
          <button
            disabled={generating}
            onClick={() => generatePlan(true)}
            className="rounded-xl bg-primary-600 text-white px-4 py-2 hover:bg-primary-700 inline-flex items-center gap-2"
          >
            <Sparkles size={16} />
            {generating ? 'Generating...' : 'Claude Periodization'}
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl p-5">
        <div className="flex items-center gap-3 mb-4">
          <CalendarDays size={18} className="text-primary-600" />
          <h2 className="font-semibold text-slate-800">Weekly Training Plan</h2>
          <input
            type="date"
            className="ml-auto rounded-xl border border-slate-300 px-3 py-2 text-sm"
            value={weekStart}
            onChange={(e) => setWeekStart(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-7 gap-3">
          {weekDays.map((day) => {
            const session = planByDate.get(day);
            return (
              <div key={day} className="border border-slate-200 rounded-xl p-3 min-h-36">
                <p className="text-sm font-medium text-slate-700">{dayLabel(day)}</p>
                {session ? (
                  <div className="mt-2 text-sm text-slate-600 space-y-1">
                    <p className="font-medium text-slate-800">{session.session_name}</p>
                    <p>{session.is_rest_day ? 'Rest day' : `${session.duration_hrs}h @ ${session.intensity_target}/10`}</p>
                    <p>{session.distance_target_km || 0} km target</p>
                    <p className="text-xs text-slate-500">{session.source}</p>
                  </div>
                ) : (
                  <p className="mt-2 text-xs text-slate-400">No plan assigned.</p>
                )}
              </div>
            );
          })}
        </div>
        {restSuggestion?.recommended_rest_day && (
          <p className="text-sm text-slate-600 mt-4">
            Recommended rest day: <span className="font-semibold">{restSuggestion.recommended_rest_day}</span> ({restSuggestion.reason})
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h2 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Target size={18} className="text-amber-500" /> Goal Setting
          </h2>
          <form onSubmit={submitGoal} className="space-y-3">
            <input
              className="w-full rounded-xl border border-slate-300 px-3 py-2"
              placeholder="Goal type (distance, sessions/week, etc.)"
              value={goalForm.goal_type}
              onChange={(e) => setGoalForm((prev) => ({ ...prev, goal_type: e.target.value }))}
              required
            />
            <div className="grid grid-cols-2 gap-3">
              <input
                className="rounded-xl border border-slate-300 px-3 py-2"
                type="number"
                step="0.01"
                placeholder="Target value"
                value={goalForm.target_value}
                onChange={(e) => setGoalForm((prev) => ({ ...prev, target_value: e.target.value }))}
              />
              <input
                className="rounded-xl border border-slate-300 px-3 py-2"
                type="number"
                placeholder="Sessions/week"
                value={goalForm.target_sessions_per_week}
                onChange={(e) => setGoalForm((prev) => ({ ...prev, target_sessions_per_week: e.target.value }))}
              />
            </div>
            <input
              className="w-full rounded-xl border border-slate-300 px-3 py-2"
              type="date"
              value={goalForm.end_date}
              onChange={(e) => setGoalForm((prev) => ({ ...prev, end_date: e.target.value }))}
              required
            />
            <textarea
              className="w-full rounded-xl border border-slate-300 px-3 py-2 min-h-20"
              placeholder="Notes"
              value={goalForm.notes}
              onChange={(e) => setGoalForm((prev) => ({ ...prev, notes: e.target.value }))}
            />
            <button className="rounded-xl bg-slate-900 hover:bg-slate-800 text-white px-4 py-2.5">Save Goal</button>
          </form>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h2 className="font-semibold text-slate-800 mb-4">Active Goals</h2>
          <div className="space-y-3">
            {goals.length ? (
              goals.map((goal) => (
                <div key={goal.id} className="border border-slate-200 rounded-xl p-3">
                  <p className="font-medium text-slate-800">{goal.goal_type}</p>
                  <p className="text-sm text-slate-600">
                    Target: {goal.target_value ?? '-'} | Sessions/week: {goal.target_sessions_per_week ?? '-'}
                  </p>
                  <p className="text-xs text-slate-500">End date: {goal.end_date} | Status: {goal.status}</p>
                </div>
              ))
            ) : (
              <p className="text-slate-400">No goals yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Planning;

