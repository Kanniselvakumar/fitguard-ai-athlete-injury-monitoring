import React, { createContext, useState, useEffect, useContext, useRef } from 'react';
import api from '../api/axios';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const initializedRef = useRef(false);

  const clearAuth = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const decodeJwtPayload = (token) => {
    try {
      const base64Payload = token.split('.')[1];
      if (!base64Payload) return null;
      const normalized = base64Payload.replace(/-/g, '+').replace(/_/g, '/');
      const json = decodeURIComponent(
        atob(normalized)
          .split('')
          .map((char) => `%${`00${char.charCodeAt(0).toString(16)}`.slice(-2)}`)
          .join('')
      );
      return JSON.parse(json);
    } catch {
      return null;
    }
  };

  const isTokenExpired = (token) => {
    const payload = decodeJwtPayload(token);
    if (!payload?.exp) return false;
    const nowSeconds = Math.floor(Date.now() / 1000);
    return payload.exp <= nowSeconds;
  };

  const refreshUser = async () => {
    const token = localStorage.getItem('token');
    if (!token || isTokenExpired(token)) {
      clearAuth();
      return null;
    }

    try {
      const response = await api.get('/auth/me');
      setUser(response.data);
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        clearAuth();
        return null;
      }
      throw error;
    }
  };

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;

    const initAuth = async () => {
      const token = localStorage.getItem('token');
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        await refreshUser();
      } catch (error) {
        console.error('Auth initialization failed', error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    localStorage.setItem('token', response.data.access_token);
    setUser(response.data.athlete);
    return response.data;
  };

  const register = async (userData) => {
    return api.post('/auth/register', userData);
  };

  const logout = () => {
    clearAuth();
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, refreshUser }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};
