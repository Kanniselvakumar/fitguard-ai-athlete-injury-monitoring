import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, AlertTriangle, Calendar, Heart, MapPin, TrendingUp } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../context/AuthContext';

const TrainingLog = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [fatigueWarning, setFatigueWarning] = useState(false);
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    duration_hrs: '',
    intensity: '',
    distance_km: '',
    heart_rate: ''
  });

  useEffect(() => {
    const checkFatigue = async () => {
      if (!user?.id) return;
      try {
        const response = await api.get(`/fatigue/latest/${user.id}`);
        if (response.data?.fatigue_score?.level === 2) {
          setFatigueWarning(true);
        }
      } catch {
        setFatigueWarning(false);
      }
    };
    checkFatigue();
  }, [user?.id]);

  const handleChange = (event) => {
    setFormData((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsLoading(true);
    try {
      const payload = {
        ...formData,
        duration_hrs: parseFloat(formData.duration_hrs),
        intensity: parseFloat(formData.intensity),
        distance_km: formData.distance_km ? parseFloat(formData.distance_km) : null,
        heart_rate: formData.heart_rate ? parseInt(formData.heart_rate, 10) : null
      };
      const response = await api.post('/training/log', payload);
      if (response.data?.log?.id) {
        await api.post('/fatigue/calculate', { log_id: response.data.log.id });
      }
      setSuccess(true);
      setTimeout(() => navigate('/dashboard'), 1800);
    } catch (error) {
      console.error('Failed to log training', error);
      alert('Failed to log session');
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-2xl mx-auto rounded-2xl border border-emerald-200 bg-emerald-50 p-8 text-center">
        <h2 className="text-xl font-bold text-emerald-700">Training Logged</h2>
        <p className="text-emerald-700 mt-2">Session stored. Redirecting to dashboard...</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Log Training Session</h1>
        <p className="text-slate-500 mt-1">Keep your risk model and recovery analytics up to date.</p>
      </div>

      {fatigueWarning && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-700 flex items-start gap-2">
          <AlertTriangle size={18} className="mt-0.5" />
          Pre-session warning: fatigue is currently high. Consider reducing intensity.
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-2xl p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block">
            <span className="text-sm text-slate-600 flex items-center gap-2 mb-1"><Calendar size={16} /> Date</span>
            <input type="date" name="date" value={formData.date} onChange={handleChange} className="w-full rounded-xl border border-slate-300 px-3 py-2" required />
          </label>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-sm text-slate-600 flex items-center gap-2 mb-1"><Activity size={16} /> Duration (hrs)</span>
              <input type="number" step="0.1" min="0.1" name="duration_hrs" value={formData.duration_hrs} onChange={handleChange} className="w-full rounded-xl border border-slate-300 px-3 py-2" required />
            </label>
            <label className="block">
              <span className="text-sm text-slate-600 flex items-center gap-2 mb-1"><TrendingUp size={16} /> Intensity (1-10)</span>
              <input type="number" min="1" max="10" name="intensity" value={formData.intensity} onChange={handleChange} className="w-full rounded-xl border border-slate-300 px-3 py-2" required />
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="block">
              <span className="text-sm text-slate-600 flex items-center gap-2 mb-1"><MapPin size={16} /> Distance (km)</span>
              <input type="number" step="0.1" name="distance_km" value={formData.distance_km} onChange={handleChange} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
            </label>
            <label className="block">
              <span className="text-sm text-slate-600 flex items-center gap-2 mb-1"><Heart size={16} /> Avg Heart Rate</span>
              <input type="number" name="heart_rate" value={formData.heart_rate} onChange={handleChange} className="w-full rounded-xl border border-slate-300 px-3 py-2" />
            </label>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-primary-600 hover:bg-primary-700 text-white py-3 font-medium disabled:opacity-60"
          >
            {isLoading ? 'Saving...' : 'Save Training Session'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default TrainingLog;

