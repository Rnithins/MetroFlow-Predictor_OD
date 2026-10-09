# MetroFlowNet Deployment Guide

This guide details how to build, test, and deploy the **MetroFlowNet Origin-Destination (OD) Passenger Flow Predictor** application to **Render**, **Docker Compose**, **Kubernetes**, and **Local Development**.

---

## 1. Deploying on Render (render.com)

Render lets you deploy both the **FastAPI Backend** and **Next.js Frontend** as managed web services. The repository includes an automated [`render.yaml`](render.yaml) Blueprint configuration.

### Prerequisites: Push Code to GitHub

Render builds directly from your GitHub repository. Ensure your latest changes are pushed:

```powershell
# In PowerShell (from MetroFlow-Predictor_OD directory)
git status
git push origin main
```

> **Note on GitHub Authentication (403 Error):**  
> If `git push` fails with `Permission denied to <user>`, update your remote with your GitHub Personal Access Token (PAT) or authenticate your GitHub account:
> ```powershell
> git remote set-url origin https://<YOUR_GITHUB_USERNAME>:<YOUR_PERSONAL_ACCESS_TOKEN>@github.com/Rnithins/MetroFlow-Predictor_OD.git
> git push origin main
> ```

---

### Option A: 1-Click Automated Blueprint (Recommended)

1. Log in to your [Render Dashboard](https://dashboard.render.com).
2. Click the **"New +"** button in the top navigation and choose **"Blueprint"**.
3. Connect your GitHub repository (`Rnithins/MetroFlow-Predictor_OD`).
4. Render automatically reads [`render.yaml`](render.yaml) and provisions two services:
   - **`metroflow-backend`** (Python 3.11 with FastAPI and PyTorch CPU)
   - **`metroflow-frontend`** (Node 18 with Next.js 14)
5. Review the plan and click **"Apply"**.
6. Render builds and launches both services. Once the backend finishes building, note its URL (e.g., `https://metroflow-backend.onrender.com`).
7. In the `metroflow-frontend` service settings under **Environment**, verify that `NEXT_PUBLIC_API_BASE_URL` points to your backend URL (`https://<backend-slug>.onrender.com/api/v1`).

---

### Option B: Manual Service Setup in Render Dashboard

If you prefer configuring services manually via the UI:

#### 1. Backend Web Service (`metroflow-backend`)
1. Click **"New +"** > **"Web Service"**.
2. Select your repository: `MetroFlow-Predictor_OD`.
3. Set configuration fields:
   - **Name**: `metroflow-backend`
   - **Region**: Any (e.g. Oregon, Frankfurt, Singapore)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. Under **Advanced** > **Health Check Path**, enter: `/health`
5. In **Environment Variables**, add:
   - `APP_NAME` = `MetroFlowNet API`
   - `API_PREFIX` = `/api/v1`
   - `SECRET_KEY` = `(click Generate to generate a secure 64-char key)`
   - `ACCESS_TOKEN_EXPIRE_MINUTES` = `180`
   - `MONGODB_URI` = `mongomock://localhost` *(or your MongoDB Atlas connection string)*
   - `MONGODB_DATABASE` = `metroflow_predictor`
   - `CORS_ORIGINS` = `*`
   - `MODEL_VERSION` = `metroflow-adaptive-fusion-v2`
   - `PYTHON_VERSION` = `3.11.9`
6. Click **Create Web Service**. Wait for the build to finish, and copy your assigned URL (e.g., `https://metroflow-backend-xxxx.onrender.com`).

#### 2. Frontend Web Service (`metroflow-frontend`)
1. Click **"New +"** > **"Web Service"**.
2. Select the same repository: `MetroFlow-Predictor_OD`.
3. Set configuration fields:
   - **Name**: `metroflow-frontend`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Runtime**: `Node`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Plan**: Free
4. Under **Advanced** > **Health Check Path**, enter: `/`
5. In **Environment Variables**, add:
   - `NODE_VERSION` = `18.20.0`
   - `NEXT_PUBLIC_API_BASE_URL` = `https://<your-backend-slug>.onrender.com/api/v1`
   - `BACKEND_URL` = `https://<your-backend-slug>.onrender.com`
6. Click **Create Web Service**.

---

### Verification Once Deployed

1. **Verify Backend Health**:
   Open in your browser: `https://<your-backend-slug>.onrender.com/health`  
   Expected JSON response: `{"status":"ok","service":"MetroFlowNet API"}`

2. **Verify Interactive API Documentation**:
   Open in your browser: `https://<your-backend-slug>.onrender.com/docs`  
   FastAPI Swagger UI will display all 34 operational endpoints.

3. **Verify Transit Frontend**:
   Open your frontend URL: `https://<your-frontend-slug>.onrender.com`  
   You will see the MetroFlowNet transit control center, live maps, OD matrix heatmaps, route optimization, and prediction composer.

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
