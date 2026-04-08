import { useState } from 'react';
import { Dumbbell, Check, X, RefreshCw } from 'lucide-react';
import api from '../utils/api';

interface ProblemState {
  expression: string;
  userAnswer: string;
  solved: boolean;
  correct: boolean | null;
  solution: any;
  steps: string[];
}

export default function Practice() {
  const [difficulty, setDifficulty] = useState('arithmetic');
  const [problems, setProblems] = useState<ProblemState[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchProblems = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/solve/practice?difficulty=${difficulty}`);
      setProblems(
        data.problems.map((expr: string) => ({
          expression: expr,
          userAnswer: '',
          solved: false,
          correct: null,
          solution: null,
          steps: [],
        }))
      );
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const checkAnswer = async (index: number) => {
    const problem = problems[index];
    if (!problem.userAnswer.trim()) return;

    try {
      const { data } = await api.post('/solve/text', { expression: problem.expression });
      const solutionValues = Object.values(data.solution);
      const expected = solutionValues.length > 0 ? String(solutionValues[0]) : '';
      const userClean = problem.userAnswer.trim().replace(/\s/g, '');
      const expectedClean = expected.replace(/\s/g, '');

      const isCorrect =
        userClean === expectedClean ||
        parseFloat(userClean) === parseFloat(expectedClean);

      setProblems((prev) =>
        prev.map((p, i) =>
          i === index
            ? { ...p, solved: true, correct: isCorrect, solution: data.solution, steps: data.steps }
            : p
        )
      );
    } catch (err) {
      console.error(err);
    }
  };

  const solvedCount = problems.filter((p) => p.solved).length;
  const correctCount = problems.filter((p) => p.correct === true).length;

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Practice Mode</h2>
        <p className="text-gray-500 mt-1">Solve random math problems and check your answers</p>
      </div>

      {/* Difficulty Selection */}
      <div className="flex items-center gap-3 mb-6">
        {['arithmetic', 'algebra', 'equations'].map((d) => (
          <button
            key={d}
            onClick={() => setDifficulty(d)}
            className={`px-4 py-2 rounded-lg font-medium capitalize transition-colors ${
              difficulty === d ? 'bg-accent-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {d}
          </button>
        ))}
        <button
          onClick={fetchProblems}
          disabled={loading}
          className="ml-auto bg-primary-500 text-white px-6 py-2 rounded-lg font-semibold hover:bg-primary-600 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          {problems.length > 0 ? 'New Problems' : 'Generate Problems'}
        </button>
      </div>

      {/* Score */}
      {problems.length > 0 && solvedCount > 0 && (
        <div className="bg-white rounded-xl border p-4 mb-6 flex items-center gap-6">
          <div className="text-sm text-gray-500">
            Solved: <strong className="text-primary-500">{solvedCount}/{problems.length}</strong>
          </div>
          <div className="text-sm text-gray-500">
            Correct: <strong className="text-green-600">{correctCount}/{solvedCount}</strong>
          </div>
          <div className="text-sm text-gray-500">
            Accuracy:{' '}
            <strong className="text-accent-600">
              {solvedCount > 0 ? Math.round((correctCount / solvedCount) * 100) : 0}%
            </strong>
          </div>
        </div>
      )}

      {/* Problems */}
      {problems.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Dumbbell size={48} className="mx-auto mb-4" />
          <p>Select a difficulty and generate problems to start practicing.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {problems.map((problem, i) => (
            <div key={i} className="bg-white rounded-xl border p-5">
              <div className="flex items-center gap-4 mb-3">
                <span className="bg-primary-500 text-white text-sm font-bold w-8 h-8 rounded-full flex items-center justify-center">
                  {i + 1}
                </span>
                <span className="font-mono text-lg text-gray-900">{problem.expression}</span>
                {problem.solved && (
                  problem.correct ? (
                    <Check size={20} className="text-green-500 ml-auto" />
                  ) : (
                    <X size={20} className="text-red-500 ml-auto" />
                  )
                )}
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="text"
                  value={problem.userAnswer}
                  onChange={(e) =>
                    setProblems((prev) =>
                      prev.map((p, j) => (j === i ? { ...p, userAnswer: e.target.value } : p))
                    )
                  }
                  onKeyDown={(e) => e.key === 'Enter' && !problem.solved && checkAnswer(i)}
                  disabled={problem.solved}
                  placeholder="Your answer..."
                  className="flex-1 px-4 py-2 border rounded-lg font-mono focus:ring-2 focus:ring-accent-500 outline-none disabled:bg-gray-50"
                />
                {!problem.solved && (
                  <button
                    onClick={() => checkAnswer(i)}
                    disabled={!problem.userAnswer.trim()}
                    className="bg-accent-500 text-white px-4 py-2 rounded-lg font-medium hover:bg-accent-600 transition-colors disabled:opacity-50"
                  >
                    Check
                  </button>
                )}
              </div>

              {problem.solved && (
                <div className="mt-3 p-3 rounded-lg bg-gray-50">
                  <div className={`text-sm font-medium mb-2 ${problem.correct ? 'text-green-600' : 'text-red-600'}`}>
                    {problem.correct ? 'Correct!' : `Incorrect. Solution: ${JSON.stringify(problem.solution)}`}
                  </div>
                  {problem.steps.length > 0 && (
                    <div className="space-y-1">
                      {problem.steps.map((step, si) => (
                        <div key={si} className="text-sm text-gray-600 font-mono">
                          {si + 1}. {step}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
