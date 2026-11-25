# Cinema Platform

Курсова робота з дисципліни «Документування програмного забезпечення та шаблони проектування», варіант 17
«Онлайн-кінотеатр»: каталог фільмів і серіалів, перегляд HLS у різній якості, підписки Free / Premium, рекомендації,
звіти для адміністратора.

Архітектура, модель даних і опис семи GoF-патернів (Builder, Proxy, Observer, Factory Method, Adapter, Strategy,
Template Method): [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Стек

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, JWT, pytest.
- База даних: PostgreSQL 16 (Docker Compose).
- Frontend: React + TypeScript + Vite, TanStack Query, hls.js, Recharts.
- Відео: ffmpeg → HLS 360p / 720p / 1080p.

## Запуск бекенду

Команди для Git Bash або PowerShell з кореня репозиторію.

```bash
docker compose up -d db
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env
.venv/Scripts/python -m alembic upgrade head
.venv/Scripts/python -m app.seed --demo-activity
.venv/Scripts/python -m uvicorn app.main:app --reload
```

На Linux / macOS замість `.venv/Scripts/python` використовуйте `.venv/bin/python`. API документація:
<http://localhost:8000/docs>.

## Демо-дані та облікові записи

Команди виконуються з теки `backend` через Python із `.venv` (наприклад, `.venv/Scripts/python -m app.seed`).

| Команда | Що робить |
|---|---|
| `python -m app.seed` | плани Free / Premium і адміністратор |
| `python -m app.seed --demo` | плюс демо-каталог: 12 жанрів, 25 фільмів, 6 серіалів |
| `python -m app.seed --demo-activity` | плюс 40 демо-користувачів з історією переглядів, Вибраним і платежами за 90 днів (повторний запуск перестворює лише їх) |
| `python -m app.tools.rebuild_stats` | перераховує статистику переглядів `title_stats` з історії |
| `python -m app.tools.demo_media` | генерує демо-відео через ffmpeg і конвертує в HLS |
| `python -m app.tools.grant_premium <email> [--days N]` | видає Premium без оплати |

Облікові записи після сіду:
- адміністратор: `ADMIN_EMAIL` / `ADMIN_PASSWORD` з `.env` (за замовчуванням `admin@example.com` / `admin12345`);
- демо-користувачі: `demo.user01@example.com` … `demo.user40@example.com`, пароль `demo12345`.

## Тести

```bash
cd backend
.venv/Scripts/python -m pytest
```

Тести використовують окрему базу `cinema_test` (створюється автоматично в тому ж контейнері PostgreSQL).

## Frontend

```bash
cd frontend
npm install
npm run dev
```
