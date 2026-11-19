# Keitaro Wrapper

Тестовое задание: обёртка над Keitaro Admin API (создаватор кампаний + редактор офферов в потоках).

Монорепозиторий под будущий Docker:

```
backend/   # FastAPI + SQLAlchemy + Alembic
frontend/  # Vue 3 + Vite + TypeScript
```

Материалы задания (`TECH/`) в git не входят.

## Требования

- Python 3.11+
- Node.js 20+

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# миграции
alembic upgrade head

uvicorn app.main:app --reload --port 8000
```

- Health: http://127.0.0.1:8000/health  
- Keitaro status: http://127.0.0.1:8000/keitaro/status  
- Create campaign: `POST /campaigns` `{name, geo, offer_id}`  
- Offer search: `GET /offers/search?q=...`  
- Streams editor: `GET/POST /campaigns/{id}/streams/...` (fetch, add/remove/pin, push, cancel)  
- Swagger: http://127.0.0.1:8000/docs  

Заполни `KEITARO_URL` и `KEITARO_API_KEY` в `backend/.env` (и при необходимости ID/имена домена, группы `FORTESTS`, источника). Проверь `/keitaro/status`.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev-сервер: http://127.0.0.1:5173  
Прокси `/api/*` → backend `:8000`.

## Дальше

1. Клиент Keitaro Admin API  
2. Создаватор кампаний  
3. Редактор streams/offers  
4. Docker Compose (backend + frontend + Postgres)

## Env

См. `backend/.env.example` (`KEITARO_URL`, `KEITARO_API_KEY`, …).
