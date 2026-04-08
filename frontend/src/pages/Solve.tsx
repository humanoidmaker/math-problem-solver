import { useState, useRef, useCallback } from 'react';
import { Upload, Type, Copy, Check, Camera } from 'lucide-react';
import api from '../utils/api';

interface SolveResult {
  id: string;
  expression: string;
  parsed: string;
  solution: Record<string, any>;
  steps: string[];
  type: string;
  confidence: number;
}

export default function Solve() {
  const [mode, setMode] = useState<'image' | 'text'>('text');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [expression, setExpression] = useState('');
  const [result, setResult] = useState<SolveResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((f: File) => {
    if (!f.type.startsWith('image/')) { setError('Please select an image file'); return; }
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError('');
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const solveImage = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/solve/image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to solve');
    } finally {
      setLoading(false);
    }
  };

  const solveText = async () => {
    if (!expression.trim()) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/solve/text', { expression: expression.trim() });
      setResult(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to solve');
    } finally {
      setLoading(false);
    }
  };

  const copySteps = () => {
    if (!result) return;
    const text = result.steps.join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const typeLabel = (t: string) => {
    const map: Record<string, string> = {
      arithmetic: 'Arithmetic',
      linear_equation: 'Linear Equation',
      quadratic_equation: 'Quadratic Equation',
      equation: 'Equation',
      expression: 'Expression',
      derivative: 'Derivative',
      integral: 'Integral',
    };
    return map[t] || t;
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Solve Math Problem</h2>
        <p className="text-gray-500 mt-1">Upload a photo or type an expression to get step-by-step solutions</p>
      </div>

      {/* Mode Toggle */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => { setMode('text'); setResult(null); setError(''); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            mode === 'text' ? 'bg-accent-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          <Type size={18} />
          Type Expression
        </button>
        <button
          onClick={() => { setMode('image'); setResult(null); setError(''); }}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            mode === 'image' ? 'bg-accent-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          <Camera size={18} />
          Upload Photo
        </button>
      </div>

      {/* Text Input Mode */}
      {mode === 'text' && (
        <div className="space-y-4">
          <div>
            <input
              type="text"
              value={expression}
              onChange={(e) => setExpression(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && solveText()}
              placeholder="e.g. 2x + 5 = 15 or x^2 - 4x + 3 = 0 or 3 + 5 * 2"
              className="w-full px-4 py-4 border-2 border-gray-200 rounded-xl text-lg focus:ring-2 focus:ring-accent-500 focus:border-transparent outline-none font-mono"
            />
            <p className="text-xs text-gray-400 mt-1">
              Supports: arithmetic, equations, quadratics (x^2), derivatives (d/dx), integrals (integral)
            </p>
          </div>
          <button
            onClick={solveText}
            disabled={!expression.trim() || loading}
            className="bg-accent-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-accent-600 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <><div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" /> Solving...</>
            ) : 'Solve'}
          </button>
        </div>
      )}

      {/* Image Upload Mode */}
      {mode === 'image' && (
        <div className="space-y-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 text-center transition-colors cursor-pointer ${
              dragOver ? 'border-accent-500 bg-accent-50' : 'border-gray-300 hover:border-accent-400'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input ref={fileInputRef} type="file" accept="image/*" className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />
            {preview ? (
              <img src={preview} alt="Preview" className="max-h-64 mx-auto rounded-lg" />
            ) : (
              <div className="space-y-3">
                <Upload className="mx-auto text-gray-400" size={48} />
                <p className="text-gray-600 font-medium">Drag and drop a math problem photo</p>
                <p className="text-gray-400 text-sm">Supports handwritten and printed math</p>
              </div>
            )}
          </div>
          <button
            onClick={solveImage}
            disabled={!file || loading}
            className="bg-accent-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-accent-600 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? (
              <><div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" /> Solving...</>
            ) : 'Solve'}
          </button>
        </div>
      )}

      {error && <div className="mt-4 bg-red-50 text-red-600 p-4 rounded-lg">{error}</div>}

      {/* Results */}
      {result && (
        <div className="mt-8 space-y-6">
          {/* Expression & Type */}
          <div className="bg-white rounded-xl border p-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Recognized Expression</h3>
              <div className="flex items-center gap-2">
                <span className="bg-accent-50 text-accent-700 px-3 py-1 rounded-full text-xs font-medium">
                  {typeLabel(result.type)}
                </span>
                <span className="text-sm text-gray-500">
                  Confidence: <strong className="text-accent-600">{result.confidence}%</strong>
                </span>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 font-mono text-lg text-center">
              {result.parsed || result.expression}
            </div>
          </div>

          {/* Solution */}
          <div className="bg-white rounded-xl border p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Solution</h3>
            <div className="bg-accent-50 rounded-lg p-4 text-center">
              {Object.entries(result.solution).map(([key, val]) => (
                <div key={key} className="text-xl font-bold text-primary-500">
                  {key === 'error' ? (
                    <span className="text-red-500">{val as string}</span>
                  ) : (
                    <span>{key} = {String(val)}</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Step-by-step */}
          <div className="bg-white rounded-xl border p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Step-by-Step Solution</h3>
              <button onClick={copySteps}
                className="flex items-center gap-1 text-sm text-gray-600 hover:text-accent-500 transition-colors">
                {copied ? <Check size={16} /> : <Copy size={16} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
            <div className="space-y-3">
              {result.steps.map((step, i) => (
                <div key={i} className="flex items-start gap-4 p-3 bg-gray-50 rounded-lg">
                  <span className="bg-accent-500 text-white text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <span className="font-mono text-gray-800">{step}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
