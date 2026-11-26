# Якість коду: тести, покриття, статичні перевірки

Цифри зафіксовано 26.11.2026 (День 6) на гілці `coursework`. Відтворити — командами з розділу 4.

## 1. Підсумок

| Показник | Бекенд | Фронтенд |
|---|---|---|
| Тестів | 597 (pytest) | 164 у 30 файлах (Vitest) |
| Покриття рядків, загалом | 98 % (4029 рядків, 83 не покрито) | 83,2 % (statements 81,7 %, branches 73,0 %) |
| Покриття ключових модулів | `app/patterns` 99,8 %, `app/services` 99,8 % | `api/` 91,2 %, `auth/` 100 %, `hooks/` 100 %, `toast/` 100 %, `player/` 98,3 % |
| Попередження в тестах | 0 | 0 |
| Лінтер | ruff check — 0 зауважень | oxlint — 0 зауважень |
| Форматування | ruff format --check — 147 файлів відформатовано | — |
| Типізація | mypy `--strict` для `app/patterns` і `app/services` — 0 помилок у 30 файлах | `tsc --noEmit` (app + node) — 0 помилок |
| Збірка | — | `npm run build` — успішно |

Цілі етапу: `patterns ≥ 90 %`, загалом `≥ 80 %` — виконано для обох частин.

## 2. Бекенд

### 2.1 Покриття

`pytest --cov=app --cov-report=term-missing`:

| Пакет | Рядків | Не покрито | Покриття |
|---|---|---|---|
| `app/patterns` | 609 | 1 | 99,8 % |
| `app/services` | 1315 | 3 | 99,8 % |
| `app/api` | 455 | 2 | 99,6 % |
| `app/core` | 234 | 3 | 98,7 % |
| `app/repositories` | 362 | 7 | 98,1 % |
| `app/models`, `app/schemas` | 575 | 0 | 100 % |
| `app` (сід, демо-дані, `main.py`) | 341 | 13 | 96,2 % |
| `app/tools` (CLI) | 138 | 54 | 60,9 % |
| **Усього** | **4029** | **83** | **98 %** |

До цього етапу: 579 тестів, 97 % загалом, `payment_gateway.py` 97 %, `recommendation.py` 98 %, одне попередження.

Найменше покриття має `app/tools/demo_media.py` (43 %): це CLI-генератор демо-відео, який запускає ffmpeg на хвилини і
перевіряється вручну (чекліст, п. 0). Чисті функції цього модуля покриті `tests/test_demo_media.py`.

### 2.2 Що додано в тести

Тести писались для гілок, що реально змінюють поведінку, а не для цифри.

| Модуль | Нові тести | Що перевіряють |
|---|---|---|
| `patterns/payment_gateway.py` (Adapter) | `test_provider_validates_its_input`, `test_unknown_provider_currency_is_a_gateway_error` | провайдер відхиляє нульову суму, чужу валюту, невідомий сценарій; адаптер не пропускає невідому валюту у відповіді |
| `patterns/recommendation.py` (Strategy) | 4 тести | видалений з каталогу тайтл не впливає на смаки; стратегія не повертає виключені тайтли, навіть якщо джерело їх віддало; компонент гібрида без додатних балів не псує нормалізацію; `limit = 0` |
| `services/subscription_service.py` | `test_granting_another_plan_expires_the_active_one` | видача іншого плану переводить активну підписку в `expired` (так описано в ER-моделі) |
| `services/video_service.py` | розпізнавання MOV / MP4 / MKV за сигнатурою; видалення відео під час конвертації | `detect_video_extension`, обробник не падає, якщо запис зник |
| `services/hls_transcoder.py` | обмеження FPS до 30, помилка ffmpeg з кодом і stderr, тайм-аут | `run_ffmpeg` перетворює всі збої на `TranscodeError` |

### 2.3 Прибрані попередження і знайдені дефекти

- `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated` — тести переведено на пакет
  `httpx2`, який рекомендує Starlette 1.x. Тестові хелпери імпортують `Response` з `httpx2`.
- `SADeprecationWarning: Result.tuples() is deprecated` (SQLAlchemy 2.1) — з'явилось під час виправлення ruff,
  замінено на `dict(result.all())`.
- **Дефект, знайдений тестами:** автоматичне «unsafe»-виправлення ruff `C416` (`{k: v for k, v in rows}` → `dict(rows)`)
  ламало звіти і рекомендації: `dict()` бачить у SQLAlchemy `Result` метод `.keys()` і пробує індексувати результат.
  22 тести впали, виправлено на `dict(rows.all())`.

### 2.4 Статичні перевірки

Конфігурація — `backend/pyproject.toml`, інструменти — у `backend/requirements-dev.txt`.

- **ruff check** з правилами `E, W, F, I, B, UP, SIM, C4, RUF`, довжина рядка 120. `RUF001–003` вимкнено: кирилиця
  в українських рядках — не «плутані символи». Виправлено: сортування імпортів, вкладені `with`, зайві `noqa`,
  змінюваний атрибут класу (`UnauthorizedError.headers` → `ClassVar`), регулярний вираз у `pytest.raises(match=...)`.
- **ruff format** — застосовано до всього бекенду один раз (52 файли), далі перевіряється `--check`.
- **mypy --strict** для `app/patterns` і `app/services` (з плагіном pydantic). Виправлено 7 помилок: типи
  `Select[...]` у продукті Builder під SQLAlchemy 2.1, тип колонки сортування, тип словника інвойсу в mock-провайдері,
  `Any` з бібліотек без типів у `core/security.py`.

## 3. Фронтенд

### 3.1 Покриття

`npm run test:coverage` (v8). Рахується весь `src/`, крім тестів, тестових хелперів `src/test/`, типів і `main.tsx`,
тому файли без жодного тесту теж входять у знаменник.

| Тека | Statements | Branches | Lines |
|---|---|---|---|
| `api/` | 91,9 % | 96,6 % | 91,2 % |
| `auth/` | 96,5 % | 92,1 % | 100 % |
| `hooks/` | 97,9 % | 95,0 % | 100 % |
| `favorites/` | 94,6 % | 85,0 % | 100 % |
| `player/` | 96,6 % | 82,9 % | 98,3 % |
| `toast/` | 98,0 % | 91,7 % | 100 % |
| `catalog/`, `billing/`, `reports/`, `routes/` | 91–100 % | 80–97 % | 96–100 % |
| `pages/` | 80,7 % | 75,4 % | 83,2 % |
| `components/` | 76,7 % | 64,1 % | 79,4 % |
| **Усього** | **81,7 %** | **73,0 %** | **83,2 %** |

До цього етапу: 87 тестів, 79 % рядків (без урахування файлів, які тести не імпортують).

### 3.2 Що додано в тести

| Файл | Що перевіряє |
|---|---|
| `api/client.test.ts` | Bearer-токен, JSON і FormData, 204, конверт помилки API, `network_error`, один спільний refresh для паралельних 401, завершення сесії при відхиленому refresh, збереження refresh-токена при недоступному сервері, ім'я файлу з `Content-Disposition` |
| `api/errors.test.ts` | переклад кодів, відсутність англійського тексту сервера для невідомих кодів, мапінг помилок валідації на поля |
| `api/adminBilling.test.ts` | параметри фільтра платежів, `limit/offset` користувачів, тіла POST-запитів, `parsePage` |
| `auth/AuthProvider.test.tsx` | гість, відновлення сесії, профіль недоступний після refresh, реєстрація з автовходом, вихід по `onSessionExpired`, `logout` |
| `auth/validation.test.ts` | правила форм входу, реєстрації, профілю (зокрема ліміт 72 байти пароля для кирилиці) |
| `favorites/cache.test.ts` | оптимістичне оновлення «Вибраного» в каталозі, деталях, історії, рекомендаціях і відкат |
| `hooks/useDismiss.test.tsx` | закриття по кліку ззовні та Escape, відписка після unmount |
| `notifications/queries.test.tsx` | лічильник непрочитаних при позначенні одного / всіх |
| `player/useHlsStream.test.ts` | hls.js (mock): унікальні якості, автозапуск і заблокований autoplay, вибір якості, відновлення після media error, повтор з поточної позиції, токен лише для `/api/`, нативний HLS, браузер без підтримки |
| `toast/toast.test.tsx` | тривалість, дедуплікація, ліміт 4, ролі `status`/`alert`, `meta.successToast` / `meta.errorToast` |
| `components/RouteErrorBoundary.test.tsx` | заміна впалої сторінки повідомленням, окремий текст для невдалого lazy-чанку |
| `App.test.tsx` | сторінка 404 і `document.title` |

## 4. Як відтворити

```bash
cd backend
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest --cov=app --cov-report=term-missing
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
.venv/Scripts/python -m mypy
```

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm run test:coverage
npm run build
```

HTML-звіт покриття фронтенду — `frontend/coverage/index.html` (тека в `.gitignore`).

## 5. Перевірка інтерфейсу (День 6)

| Пункт | Що зроблено |
|---|---|
| Терміни | Усі тексти українською: «Вибране», «Преміум», «Безкоштовний», «Сезон», «Епізод», «Електронна пошта». Назви планів у БД і текстах сповіщень — теж українські |
| 404 і помилки маршрутів | `NotFoundPage` для невідомих адрес; `RouteErrorBoundary` у `Layout` для помилок рендеру і невдалих lazy-чанків |
| Тости | Єдиний механізм: `meta.successToast` / `meta.errorToast` у мутаціях, глобальний `MutationCache`, `Toaster` з `aria-live`. Помилки форм лишаються біля полів |
| Адаптивність | Мобільне меню під шапкою (раніше на ширині < 640 px навігації не було взагалі), панель сповіщень не виходить за край на 375 px, таблиці гортаються всередині блоку |
| Порожні стани і скелетони | Скелетони для адмін-таблиць, жанрів, історії платежів і сторінки тайтлу; порожній стан для списку користувачів |
| Доступність | `alt` у постерів, підписи у всіх полях форм, видимий фокус для посилань і кнопок (`:focus-visible`), `aria-label` для логотипа на мобільному |
| Заголовок вкладки | `useDocumentTitle` на кожній сторінці: «Назва · Cinema Platform»; favicon — власний SVG |

Ручна перевірка цих пунктів — розділ 9 у [MANUAL_TEST.md](MANUAL_TEST.md).
