import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Register = () => {
  const { register, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    age: '',
    sport: '',
    weight: '',
    height: '',
    previous_injuries_count: '',
    injury_history: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const onChange = (event) => {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await register({
        ...form,
        age: parseInt(form.age || 25, 10),
        weight: parseFloat(form.weight || 70),
        height: parseFloat(form.height || 175),
        previous_injuries_count: parseInt(form.previous_injuries_count || 0, 10)
      });
      await login(form.email, form.password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.message || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center">
      <div className="w-full max-w-2xl bg-white border border-slate-200 rounded-2xl p-8">
        <div className="text-center mb-6">
          <div className="inline-flex w-14 h-14 rounded-full bg-primary-100 text-primary-600 items-center justify-center mb-3">
            <UserPlus size={28} />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Create Account</h1>
          <p className="text-slate-500 text-sm mt-1">Set your athlete profile and start tracking</p>
        </div>

        {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-red-700 text-sm">{error}</div>}

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input name="name" value={form.name} onChange={onChange} required placeholder="Full name" className="rounded-xl border border-slate-300 px-3 py-2" />
            <input name="sport" value={form.sport} onChange={onChange} placeholder="Sport" className="rounded-xl border border-slate-300 px-3 py-2" />
            <input name="email" type="email" value={form.email} onChange={onChange} required placeholder="Email" className="rounded-xl border border-slate-300 px-3 py-2" />
            <input name="password" type="password" value={form.password} onChange={onChange} required minLength={6} placeholder="Password" className="rounded-xl border border-slate-300 px-3 py-2" />
            <input name="age" type="number" value={form.age} onChange={onChange} placeholder="Age" className="rounded-xl border border-slate-300 px-3 py-2" />
            <input name="weight" type="number" step="0.1" value={form.weight} onChange={onChange} placeholder="Weight (kg)" className="rounded-xl border border-slate-300 px-3 py-2" />
            <input name="height" type="number" step="0.1" value={form.height} onChange={onChange} placeholder="Height (cm)" className="rounded-xl border border-slate-300 px-3 py-2" />
            <input name="previous_injuries_count" type="number" min="0" value={form.previous_injuries_count} onChange={onChange} placeholder="Previous injuries count" className="rounded-xl border border-slate-300 px-3 py-2" />
          </div>
          <textarea
            name="injury_history"
            value={form.injury_history}
            onChange={onChange}
            placeholder="Injury history (optional)"
            className="w-full rounded-xl border border-slate-300 px-3 py-2 min-h-20"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-primary-600 hover:bg-primary-700 text-white py-3 font-medium disabled:opacity-60"
          >
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="text-sm text-center text-slate-500 mt-5">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;

