import { useState, useEffect } from 'react';
import { Calculator, TrendingUp, Camera, Type } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import api from '../utils/api';

interface Stats {
  total_problems: number;
  avg_confidence: number;
  by_type: Record<string, number>;
  by_source: Record<string, number>;
}

const TYPE_COLORS = ['#f59e0b', '#1e293b', '#3b82f6', '#22c55e', '#ef4444', '#8b5cf6', '#ec4899'];

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/solve/stats').then(({ data }) => setStats(data)).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin h-8 w-8 border-4 border-accent-500 border-t-transparent rounded-full" /></div>;
  }

  if (!stats) return null;

  const typeData = Object.entries(stats.by_type).map(([name, value]) => ({ name, value }));
  const sourceData = Object.entries(stats.by_source).map(([name, value]) => ({ name: name === 'image' ? 'Photo' : 'Text', value }));

  const cards = [
    { label: 'Problems Solved', value: stats.total_problems, icon: Calculator, color: 'bg-accent-500' },
    { label: 'Avg Confidence', value: `${stats.avg_confidence}%`, icon: TrendingUp, color: 'bg-green-500' },
    { label: 'From Photos', value: stats.by_source.image || 0, icon: Camera, color: 'bg-blue-500' },
    { label: 'From Text', value: stats.by_source.text || 0, icon: Type, color: 'bg-purple-500' },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>

      <div className="grid grid-cols-4 gap-4 mb-8">
        {cards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-white rounded-xl border p-5">
            <div className="flex items-center gap-3">
              <div className={`${color} text-white p-2.5 rounded-lg`}><Icon size={20} /></div>
              <div>
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-xl font-bold text-gray-900">{value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Problem Types Distribution */}
        {typeData.length > 0 && (
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Difficulty Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={typeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Source Distribution */}
        {sourceData.length > 0 && (
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-semibold text-gray-900 mb-4">Input Source</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={sourceData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label>
                  {sourceData.map((_, i) => (
                    <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
