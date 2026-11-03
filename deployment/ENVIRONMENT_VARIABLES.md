# SmartAttend — Environment Variables Catalog

This document details every environment variable used across the SmartAttend stack.

---

## 1. Backend Environment Variables (`backend2/.env` or `deployment/.env`)

| Variable | Description | Required? | Default / Example Value |
| :--- | :--- | :---: | :--- |
| `APP_NAME` | Service display name | No | `"SmartAttend AIoT Backend2"` |
| `APP_ENV` | Environment mode (`development`, `staging`, `production`) | No | `"development"` |
| `APP_PORT` | Backend port | No | `8002` |
| `DATABASE_URL` | SQLAlchemy database connection URI | **Yes** | `"sqlite:///./smartattend.db"` (Dev) or `"postgresql://..."` (Prod) |
| `SECRET_KEY` | 64-character random string for signing JWT tokens | **Yes** | `"generate-a-strong-random-secret-key-2026"` |
| `ALGORITHM` | JWT hashing algorithm | No | `"HS256"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes | No | `1440` (24 hours) |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins | **Yes** | `"http://localhost:3000,https://smartattend.vercel.app"` |
| `STORAGE_DRIVER` | File storage adapter (`local` or `supabase`) | No | `"local"` |
| `UPLOAD_DIR` | Directory for local file storage | No | `"uploads"` |
| `SCRFD_MODEL_PATH` | Path to SCRFD-10G ONNX model weights | No | `"weights/scrfd_10g_bnkps.onnx"` |
| `SCRFD_DEVICE` | Execution device for ONNX Runtime (`cpu` or `cuda`) | No | `"cpu"` |
| `FACE_RECOGNITION_THRESHOLD` | Cosine similarity threshold for True Positive face match | No | `0.70` |
| `FACE_AMBIGUITY_THRESHOLD` | Margin score threshold triggering ambiguity flag | No | `0.08` |
| `DEVICE_API_KEY` | Shared secret key for ESP8266 IoT hardware nodes | No | `"smartattend-esp-secret-key-2026"` |

---

## 2. Frontend Environment Variables (`.env.local` or Vercel Settings)

| Variable | Description | Required? | Default / Example Value |
| :--- | :--- | :---: | :--- |
| `NEXT_PUBLIC_API_URL` | Target FastAPI base endpoint including `/api` | **Yes** | `"http://localhost:8002/api"` (Dev) or `"https://api.yourdomain.com/api"` (Prod) |
| `NEXT_PUBLIC_SUPABASE_URL` | Public Supabase project URL | No | `"https://ynpvbxtrfbcwficiwphg.supabase.co"` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public anonymous client API key | No | `"sb_publishable_..."` |

> [!CAUTION]
> Never set `SUPABASE_SERVICE_ROLE_KEY` or `DATABASE_URL` with a `NEXT_PUBLIC_` prefix. Next.js inlines variables prefixed with `NEXT_PUBLIC_` into browser JavaScript bundles.
