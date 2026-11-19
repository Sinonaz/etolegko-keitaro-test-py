# Keitaro Wrapper

Тестовое задание: обёртка над Keitaro Admin API  
(создаватор кампаний + редактор офферов в потоках).

```
backend/   # FastAPI + SQLAlchemy + Alembic
frontend/  # Vue 3 + Vite + TypeScript + Naive UI
```

Материалы задания (`TECH/`) в git не входят.

## Требования

- Docker + Docker Compose **или**
- Python **3.12+**, Node.js **20+**, npm

Нужен доступ к Keitaro: `KEITARO_URL` (origin админки) и `KEITARO_API_KEY`  
(Профиль → API keys в трекере).

## Быстрый старт (Docker)

```bash
cp .env.example .env
# обязательные: KEITARO_URL, KEITARO_API_KEY
# опционально: KEITARO_DOMAIN_ID / GROUP_ID / SOURCE_ID
#   или имена KEITARO_*_NAME (группа по умолчанию FORTESTS;
#   если traffic source не найден — используется 0)

docker compose up --build
```

Открыть UI: http://127.0.0.1:8080

Что поднимается:

| Сервис    | Роль                                      |
|-----------|-------------------------------------------|
| `db`      | Postgres 16                               |
| `backend` | FastAPI; при старте `alembic upgrade head` |
| `frontend`| nginx: UI + proxy `/api/*` → backend      |

Остановка: `docker compose down`  
Сброс БД: `docker compose down -v`

После смены `.env` пересоздайте backend:

```bash
docker compose up -d --force-recreate backend
```

Проверка связи с Keitaro:

```bash
curl -s http://127.0.0.1:8080/api/keitaro/status
# ожидается: "configured": true, "reachable": true
```

## Миграции

Миграции — Alembic, каталог `backend/alembic/versions/`.

**Docker:** применяются автоматически в `backend/entrypoint.sh` перед uvicorn.

**Локально (из `backend/`):**

```bash
alembic upgrade head          # применить
alembic current               # текущая ревизия
alembic history               # история
```

SQLite по умолчанию (`DATABASE_URL=sqlite:///./app.db`).  
В Compose backend получает Postgres:

`postgresql+psycopg2://keitaro:keitaro@db:5432/keitaro`

## Локальная разработка без Docker

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env     # заполнить KEITARO_* и при необходимости DATABASE_URL

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API: http://127.0.0.1:8000  
Swagger: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: http://127.0.0.1:5173  
Vite проксирует `/api/*` → `http://127.0.0.1:8000` (префикс `/api` снимается).

## Env

См. корневой `.env.example` и `backend/.env.example`.

| Переменная | Назначение |
|------------|------------|
| `KEITARO_URL` | Origin трекера, без `/admin_api/...` |
| `KEITARO_API_KEY` | Ключ Admin API |
| `KEITARO_DOMAIN_ID` / `KEITARO_DOMAIN_NAME` | Домен кампании (если пусто — первый активный) |
| `KEITARO_GROUP_ID` / `KEITARO_GROUP_NAME` | Группа (по умолчанию имя `FORTESTS`) |
| `KEITARO_SOURCE_ID` / `KEITARO_SOURCE_NAME` | Traffic source; если не найден — `0` |
| `KEITARO_WHITE_PAGE_URL` | Редирект geo-потока (по умолчанию Google) |
| `DATABASE_URL` | SQLite локально; в Docker переопределяется |

## API (кратко)

Через UI/nginx пути с префиксом `/api`  
(напрямую к backend — без `/api`):

- `GET /health`
- `GET /keitaro/status`
- `POST /campaigns` — `{name, geo, offer_id}`
- `GET /offers/search?q=...`
- `GET/POST /campaigns/{id}/streams/...` — fetch / add / remove / pin / push / cancel

## Что умеет приложение

1. **Create campaign** — кампания в Keitaro с двумя потоками:  
   geo → Google, default → выбранный оффер; домен/группа/источник из env или резолва.
2. **Streams editor** — офферы потока, soft-remove / bring-back, equal share + pin, push / cancel.
