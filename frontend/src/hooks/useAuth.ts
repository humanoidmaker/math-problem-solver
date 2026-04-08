import { useState, useEffect } from 'react';
import api from '../utils/api';

interface User {
  id: string;
  name: string;
  email: string;
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('mathlens_user');
    const token = localStorage.getItem('mathlens_token');
    if (stored && token) {
      setUser(JSON.parse(stored));
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await api.post('/auth/login', { email, password });
    localStorage.setItem('mathlens_token', data.token);
    localStorage.setItem('mathlens_user', JSON.stringify(data.user));
    setUser(data.user);
    return data;
  };

  const register = async (name: string, email: string, password: string) => {
    const { data } = await api.post('/auth/register', { name, email, password });
    localStorage.setItem('mathlens_token', data.token);
    localStorage.setItem('mathlens_user', JSON.stringify(data.user));
    setUser(data.user);
    return data;
  };

  const logout = () => {
    localStorage.removeItem('mathlens_token');
    localStorage.removeItem('mathlens_user');
    setUser(null);
  };

  return { user, loading, login, register, logout };
}
