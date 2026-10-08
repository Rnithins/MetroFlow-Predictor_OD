# MetroFlowNet Deployment Guide

This guide details how to build, test, and deploy the **MetroFlowNet Origin-Destination (OD) Passenger Flow Predictor** application to **Render**, **Docker Compose**, **Kubernetes**, and **Local Development**.

---

## 1. Deploying on Render (render.com)

You can deploy the entire stack to Render using either the **Automated Blueprint** (recommended) or **Manual Setup**.

### Method A: Automated Blueprint (1-Click)
1. Push your code to a GitHub/GitLab repository.
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **"New +"** in the top navigation and select **"Blueprint"**.
4. Connect your repository. Render will automatically detect [`render.yaml`](render.yaml).
5. Render will configure:
   - **`metroflow-backend`** (Python 3.11 web service with PyTorch AFFN model)
   - **`metroflow-frontend`** (Node.js Next.js 14 transit control center)
   - Automatic cross-service environment variables (`NEXT_PUBLIC_API_BASE_URL` & `BACKEND_URL`)
6. Click **"Apply"**. Both services will build and deploy automatically!

### Method B: Manual Dashboard Setup on Render

#### Step 1: Deploy Backend Web Service
1. In Render, click **"New +"** > **"Web Service"**.
2. Connect your repo and set:
   - **Name**: `metroflow-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
3. Add Environment Variables:
   - `APP_NAME` = `MetroFlowNet API`
   - `API_PREFIX` = `/api/v1`
   - `SECRET_KEY` = `(click Generate)`
   - `CORS_ORIGINS` = `*`
   - `MONGODB_URI` = `mongomock://localhost` *(or your MongoDB Atlas connection string)*
   - `MONGODB_DATABASE` = `metroflow_predictor`
   - `MODEL_VERSION` = `metroflow-adaptive-fusion-v2`
4. Click **Create Web Service**. Note the deployed URL (e.g. `https://metroflow-backend.onrender.com`).

#### Step 2: Deploy Frontend Web Service
1. In Render, click **"New +"** > **"Web Service"**.
2. Connect your repo and set:
   - **Name**: `metroflow-frontend`
   - **Root Directory**: `frontend`
   - **Runtime**: `Node`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Health Check Path**: `/`
3. Add Environment Variables:
   - `NODE_VERSION` = `18.20.0`
   - `NEXT_PUBLIC_API_BASE_URL` = `https://metroflow-backend.onrender.com/api/v1` *(replace with your actual backend URL)*
   - `BACKEND_URL` = `https://metroflow-backend.onrender.com`
4. Click **Create Web Service**.

---

## 2. Deploy with Docker Compose (Local & VPS)

The full system (FastAPI backend with PyTorch AFFN model, Next.js frontend, MongoDB, and PostgreSQL) can be deployed with Docker Compose.

### Prerequisites
- [Docker Engine](https://docs.docker.com/get-docker/) (20.10+)
- [Docker Compose](https://docs.docker.com/compose/) (v2.0+)

### Commands

```bash
# Navigate to the project root
cd MetroFlow-Predictor_OD

# Build and start all 4 containers in detached mode
docker-compose up --build -d

# Check status of running containers
docker-compose ps

# View real-time logs
docker-compose logs -f
```

### Services & Port Mappings

| Service | Internal Port | Host URL | Description |
|---|---|---|---|
| **Frontend** | 3000 | `http://localhost:3000` | Next.js 14 Transit Dashboard & Control Center |
| **Backend** | 8000 | `http://localhost:8000` | FastAPI REST API (Swagger at `/docs`) |
| **MongoDB** | 27017 | `mongodb://localhost:27017` | NoSQL primary store for flows, stations, OD matrices |
| **PostgreSQL**| 5432 | `postgresql://localhost:5432` | Relational operational schema storage |

To stop the services:
```bash
docker-compose down
```

---

## 2. Local Development Deployment

If you are developing locally on Windows PowerShell:

```powershell
# Run the automated launch script (starts both backend and frontend in separate terminals)
.\start-dev.ps1
```

### Manual Local Startup

**Terminal 1: Backend**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000
```

**Terminal 2: Frontend**
```powershell
cd frontend
npm run dev
```

Visit `http://localhost:3000` in your browser.

---

## 3. Kubernetes Deployment (K8s)

Kubernetes manifests are located in `k8s/deployment.yaml`.

```bash
# 1. Create secret for JWT authentication
kubectl create secret generic metroflownet-secrets \
  --from-literal=secret-key="your-production-secret-key-change-me"

# 2. Apply deployment manifests
kubectl apply -f k8s/deployment.yaml

# 3. Verify rollout status
kubectl rollout status deployment/metroflownet-backend
kubectl rollout status deployment/metroflownet-frontend

# 4. Get services and external IP
kubectl get svc
```

---

## 4. Production Environment Variables Reference

### Backend (`backend/.env`)

```ini
APP_NAME=MetroFlowNet API
API_PREFIX=/api/v1
SECRET_KEY=generate-a-strong-random-hex-key
ACCESS_TOKEN_EXPIRE_MINUTES=180
MONGODB_URI=mongodb://mongo:27017
MONGODB_DATABASE=metroflow_predictor
POSTGRES_URI=postgresql://metro_user:metro_pass@postgres:5432/metroflownet
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://yourdomain.com
MODEL_VERSION=metroflow-adaptive-fusion-v2
OPENWEATHERMAP_API_KEY=your_openweathermap_api_key
OTD_DELHI_API_KEY=your_otd_delhi_api_key
```

### Frontend (`frontend/.env.local`)

```ini
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
BACKEND_URL=http://localhost:8000
```

---

## 5. Verification & Live Health Checks

Once deployed, run the automated live test suite to verify all 34 REST API endpoints:

```bash
cd backend
python test_all_apis_live.py
```

Expected result:
```
=======================================================
Total API Endpoints Tested: 34
Passed: 34/34 (100.0%)
Failed: 0/34
=======================================================
```
