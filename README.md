# MathLens — Math Problem Solver from Photo

AI-powered math problem solver that reads handwritten and printed math from photos and provides step-by-step solutions using symbolic computation.

## Tech Stack

- **Backend**: Python FastAPI + PyTorch + TrOCR + SymPy
- **Frontend**: React + TypeScript + Tailwind CSS + Recharts
- **Database**: MongoDB
- **ML Model**: microsoft/trocr-base-handwritten (OCR) + SymPy (solver)

## GPU Requirements

- NVIDIA GPU with CUDA 11.8+ recommended for image OCR
- Minimum 4GB VRAM for TrOCR base model
- CPU fallback supported (text input mode works without GPU)
- Text-based solving uses SymPy (CPU only, very fast)

## Quick Start

```bash
cd apps/math-problem-solver

cp backend/.env.example backend/.env
# Edit backend/.env with your settings

docker-compose up --build

# Access at http://localhost:3000
```

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Features

- Two input modes: Upload photo or type expression
- OCR for handwritten and printed math
- Step-by-step solutions styled like a math notebook
- Supports: arithmetic, linear equations, quadratic equations, derivatives, integrals
- Practice mode with random problems by difficulty
- Problem history with expandable step details
- Dashboard with type distribution and accuracy stats
- Copy solution steps

## Supported Problem Types

- **Arithmetic**: 24 + 37, 12 * 15, (15 + 9) * 3
- **Linear Equations**: 2x + 5 = 15, 3x - 7 = 20
- **Quadratic Equations**: x^2 - 4x + 3 = 0
- **Derivatives**: d/dx x^2 + 3x
- **Integrals**: integral x^2 + 1
- **Expressions**: simplify and factor

## API Endpoints

- `POST /api/solve/image` — Solve from photo
- `POST /api/solve/text` — Solve from typed expression
- `GET /api/solve/history` — Problem history
- `GET /api/solve/stats` — Usage statistics
- `GET /api/solve/practice` — Random practice problems

---

Built by [Humanoid Maker](https://www.humanoidmaker.com)


## Deployment

### Docker Compose (Easiest)

```bash
# Clone the repository
git clone https://github.com/humanoidmaker/math-problem-solver.git
cd math-problem-solver

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### PM2 (Production Process Manager)

```bash
# Install PM2 globally
npm install -g pm2

# Install dependencies
cd backend && pip install -r requirements.txt && cd ..
cd frontend && npm install && cd ..

# Start all services
pm2 start ecosystem.config.js

# Monitor
pm2 monit

# View logs
pm2 logs

# Stop all
pm2 stop all

# Auto-restart on reboot
pm2 startup
pm2 save
```

### Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/mongodb.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check status
kubectl get pods -n math-problem-solver

# View logs
kubectl logs -f deployment/backend -n math-problem-solver

# Scale
kubectl scale deployment/backend --replicas=3 -n math-problem-solver
```

### Manual Setup

**1. Database:**
```bash
# Start MongoDB
mongod --dbpath /data/db
```

**2. Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv/Scripts/activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database URL and secrets


uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**3. Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**4. Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## License

MIT License — Copyright (c) 2026 Humanoid Maker (www.humanoidmaker.com)
