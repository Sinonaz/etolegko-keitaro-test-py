# Keitaro Wrapper

Тестовое задание: обёртка над Keitaro Admin API (создаватор кампаний + редактор офферов в потоках).

```
backend/   # FastAPI + SQLAlchemy + Alembic
frontend/  # Vue 3 + Vite + TypeScript
```

Материалы задания (`TECH/`) в git не входят.

## Docker (рекомендуется)

```bash
cp .env.example .env
# заполнить KEITARO_URL и KEITARO_API_KEY

docker compose up --build
```

Открыть: http://127.0.0.1:8080  

- UI (nginx) проксирует `/api/*` → backend  
- Postgres в сервисе `db`  
- При старте backend гоняет `alembic upgrade head`

Остановка: `docker compose down`  
Сброс БД: `docker compose down -v`

## Локальная разработка без Docker

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # или свой backend/.env

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev-сервер: http://127.0.0.1:5173 (прокси `/api` → `:8000`).

## API

- Health: `/health`  
- Keitaro status: `/keitaro/status`  
- Create campaign: `POST /campaigns` `{name, geo, offer_id}`  
- Offer search: `GET /offers/search?q=...`  
- Streams editor: `/campaigns/{id}/streams/...`  
- Swagger (backend напрямую): http://127.0.0.1:8000/docs  

## Env

См. `.env.example` / `backend/.env.example`.
