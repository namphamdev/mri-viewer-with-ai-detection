# MRI Viewer with AI Detection

A web-based MRI DICOM viewer with AI-powered anomaly detection. The application proxies DICOM images from a PACS server, displays them in an interactive viewer, and provides AI analysis with heatmap overlays highlighting potential anomalies.

## Architecture

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Frontend   │──────▶│   Backend    │──────▶│  PACS Server │
│  React+Vite  │ :3000 │   FastAPI    │ :8000 │  (DICOMweb)  │
│   (nginx)    │◀──────│   Python     │◀──────│              │
└──────────────┘       └──────────────┘       └──────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  AI Engine   │
                       │  (PyTorch)   │
                       └──────────────┘
```

- **Frontend**: React 18 + TypeScript + Tailwind CSS, served via nginx in production
- **Backend**: FastAPI (Python 3.12) — DICOM proxy + AI analysis API
- **AI Engine**: PyTorch-based anomaly detection with heatmap generation

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- For local development: Node.js 20+, Python 3.12+

## Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd mri-viewer

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Health check: http://localhost:8000/api/health
```

To stop:

```bash
docker-compose down
```

## Development Setup (Without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/studies/{study}/series/{series}/metadata` | Get series metadata |
| `GET` | `/api/studies/{study}/series/{series}/instances` | List instances in a series |
| `GET` | `/api/studies/{study}/series/{series}/instances/{instance}/frames/{frame}` | Get a frame as PNG |
| `POST` | `/api/ai/analyze` | Run AI anomaly detection |

### AI Analysis Request

```json
POST /api/ai/analyze
{
  "study_uid": "1.2.840...",
  "series_uid": "1.2.392...",
  "instance_uid": null,
  "sensitivity": 0.5,
  "analysis_type": "anomaly"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MRI_PACS_BASE_URL` | `https://pacs.mids.com.vn/pacs/rs` | PACS server DICOMweb URL |
| `MRI_CORS_ORIGINS` | `["http://localhost:5173","http://localhost:3000"]` | Allowed CORS origins |
| `MRI_DEBUG` | `false` | Enable debug logging |

## Project Structure

```
├── docker-compose.yml       # Multi-service orchestration
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py          # FastAPI entry point
│       ├── config.py         # Environment-based settings
│       ├── routers/
│       │   ├── health.py     # Health check endpoint
│       │   ├── dicom.py      # DICOM proxy endpoints
│       │   └── ai.py         # AI analysis endpoint
│       ├── ai/
│       │   ├── detector.py   # Detection pipeline
│       │   ├── model.py      # PyTorch model
│       │   ├── preprocessing.py
│       │   └── postprocessing.py
│       └── services/
│           ├── pacs_client.py
│           └── dicom_utils.py
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    └── src/
        ├── App.tsx
        ├── api/              # API client
        └── components/       # React components
```

## Screenshots

<!-- Add screenshots here -->

## License

Private — All rights reserved.
