# Cinema Platform — фронтенд

SPA онлайн-кінотеатру: React 19, TypeScript, Vite, React Router, TanStack Query, Tailwind CSS.
Адмін-частина — розділ `/admin` у цьому ж застосунку.

## Вимоги

- Node.js 20.19+ або 22.12+ (npm входить у комплект)
- Запущений бекенд на `http://localhost:8000` (див. кореневий README)

## Запуск

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Застосунок відкривається на <http://localhost:5173>. Запити до `/api` dev-сервер проксіює на бекенд
`http://localhost:8000`, тому CORS у режимі розробки не потрібен.

Бекенд (база даних — з кореня репозиторію, решта — з каталогу `backend/` в активованому `.venv`):

```bash
docker compose up -d db
cd backend
python -m alembic upgrade head
python -m app.seed
python -m uvicorn app.main:app --reload
```

## Змінні середовища

| Змінна | Призначення | За замовчуванням |
|---|---|---|
| `VITE_API_URL` | Базова адреса API. Порожнє значення — запити йдуть на той самий origin (`/api`) через proxy dev-сервера | порожньо |

Якщо фронтенд розгортається окремо від бекенда, вкажіть повну адресу, наприклад `VITE_API_URL=https://api.example.com`.

## Команди

| Команда | Що робить |
|---|---|
| `npm run dev` | dev-сервер з HMR на порту 5173 |
| `npm run build` | перевірка типів (`tsc -b`) і продакшн-збірка в `dist/` |
| `npm run preview` | локальний перегляд зібраної версії |
| `npm run lint` | перевірка коду oxlint |
| `npm test` | тести Vitest + Testing Library (одноразовий прогін) |
| `npm run test:watch` | тести в режимі спостереження |

## Структура `src/`

| Каталог | Вміст |
|---|---|
| `api/` | HTTP-клієнт (Bearer-токен, автоматичний refresh при 401), ендпоінти, тексти помилок |
| `auth/` | `AuthProvider` і `useAuth`, клієнтська валідація форм |
| `components/` | Layout, хедер, поля форм, картки профілю |
| `pages/` | Головна, вхід, реєстрація, профіль, адмін-панель, 404 |
| `routes/` | Дерево маршрутів, `ProtectedRoute`, `AdminRoute`, `GuestRoute` |
| `types/` | TypeScript-типи, що відповідають Pydantic-схемам бекенда |
| `test/` | налаштування Vitest і допоміжні функції для тестів |

## Авторизація

- Access-токен зберігається лише в памʼяті вкладки, refresh-токен — у `localStorage`.
- Під час старту застосунок відновлює сесію: `POST /api/auth/refresh`, потім `GET /api/users/me`.
- Якщо запит повертає 401, клієнт один раз оновлює токени і повторює запит. Якщо оновити не вдалося,
  сесія завершується і користувача перенаправлено на `/login`.
- Після входу користувач повертається на сторінку, з якої його перенаправили.
