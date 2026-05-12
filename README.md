# Industrial RAG (Reference Implementation)

## Backend

```bash
pip install -e .
uvicorn app.api.main:app --reload
```

## Frontend (React + Vite + Tailwind)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Features

- Chat page with conversation history sidebar.
- Dashboard page for conversation analytics.
- Settings page with OpenRouter API key + model.
- Upload control included in UI (backend currently needs multipart ingest endpoint for real file upload).
