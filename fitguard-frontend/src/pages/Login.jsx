import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Activity } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const onSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to login');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl p-8">
        <div className="text-center mb-6">
          <div className="inline-flex w-14 h-14 rounded-full bg-primary-100 text-primary-600 items-center justify-center mb-3">
            <Activity size={28} />
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Sign In</h1>
          <p className="text-slate-500 text-sm mt-1">Access your dashboard and training insights</p>
        </div>

        {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-2 text-red-700 text-sm">{error}</div>}

        <form onSubmit={onSubmit} className="space-y-4">
          <input
            type="email"
            required
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2"
          />
          <input
            type="password"
            required
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-slate-300 px-3 py-2"
          />
          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-primary-600 hover:bg-primary-700 text-white py-3 font-medium disabled:opacity-60"
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="text-sm text-center text-slate-500 mt-5">
          Do not have an account?{' '}
          <Link to="/register" className="text-primary-600 hover:text-primary-700 font-medium">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Login;

