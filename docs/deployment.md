# Deployment Guide

## Environment Variables

### Backend

```env
APP_NAME=MetroFlow Predictor API
API_PREFIX=/api/v1
SECRET_KEY=replace-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=180
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net
MONGODB_DATABASE=metroflow_predictor
CORS_ORIGINS=https://your-frontend-domain.com
MODEL_VERSION=metroflow-baseline-regression-v2
```

### Frontend

```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend-domain.com/api/v1
```

## Recommended Hosting

### Frontend

- Vercel
- Netlify

### Backend

- Render
- Railway
- AWS App Runner
- EC2 / Docker host

### Database

- MongoDB Atlas

## Vercel + Render Setup

### Frontend on Vercel

1. Import the `frontend/` directory as a Vercel project.
2. Set `NEXT_PUBLIC_API_BASE_URL`.
3. Build command: `npm run build`
4. Output: default Next.js output

### Backend on Render

1. Create a web service from `backend/`.
2. Runtime: Python
3. Build command:

```bash
pip install -r requirements.txt
```

4. Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Set backend environment variables from the block above.
6. Add your Vercel domain to `CORS_ORIGINS`.

## AWS Path

1. Deploy the frontend to Vercel or S3 + CloudFront.
2. Deploy the backend with App Runner, ECS, or EC2.
3. Store `SECRET_KEY` and `MONGODB_URI` in Secrets Manager or Parameter Store.
4. Use MongoDB Atlas or a self-managed MongoDB deployment.

## CI/CD Checks

Run these on every push:

```bash
cd backend && .\.venv\Scripts\python.exe -m pytest
cd frontend && npm run build
```

Optional GitHub Actions steps:

1. Install Python dependencies
2. Run backend tests
3. Install frontend dependencies
4. Run frontend build
5. Deploy on main branch
