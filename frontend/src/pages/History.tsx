import { useState, useEffect } from 'react';
import { Clock, Calculator, Camera, Type } from 'lucide-react';
import api from '../utils/api';

interface Problem {
  id: string;
  expression: string;
  parsed: string;
  type: string;
  source: string;
  confidence: number;
  solution: Record<string, any>;
  steps: string[];
  created_at: string;
}

export default function HistoryPage() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    api.get('/solve/history').then(({ data }) => setProblems(data)).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="animate-spin h-8 w-8 border-4 border-accent-500 border-t-transparent rounded-full" /></div>;
  }

  const typeLabel = (t: string) => {
    const map: Record<string, string> = {
      arithmetic: 'Arithmetic', linear_equation: 'Linear Eq', quadratic_equation: 'Quadratic',
      equation: 'Equation', expression: 'Expression', derivative: 'Derivative', integral: 'Integral',
    };
    return map[t] || t;
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Problem History</h2>
      {problems.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Calculator size={48} className="mx-auto mb-4" />
          <p>No problems solved yet. Try the Solve or Practice page.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {problems.map((p) => (
            <div
              key={p.id}
              className="bg-white rounded-xl border p-5 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setExpanded(expanded === p.id ? null : p.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  {p.source === 'image' ? <Camera size={16} className="text-accent-500" /> : <Type size={16} className="text-accent-500" />}
                  <span className="font-mono text-gray-900">{p.parsed || p.expression}</span>
                  <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">{typeLabel(p.type)}</span>
                </div>
                <div className="flex items-center gap-1 text-gray-400 text-sm ml-4">
                  <Clock size={14} />
                  {new Date(p.created_at).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short' })}
                </div>
              </div>

              {/* Solution preview */}
              <div className="mt-2 text-sm text-gray-600">
                Solution: {Object.entries(p.solution).map(([k, v]) => `${k} = ${v}`).join(', ')}
              </div>

              {/* Expanded steps */}
              {expanded === p.id && p.steps.length > 0 && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg space-y-1">
                  {p.steps.map((step, i) => (
                    <div key={i} className="text-sm font-mono text-gray-700">
                      {i + 1}. {step}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
