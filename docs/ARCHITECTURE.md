# Архітектура Cinema Platform

## 1. Актори і Use Cases

```mermaid
flowchart LR
    G([Гість])
    U([Користувач])
    P([Преміум-користувач])
    A([Адміністратор])
    PG([Платіжний шлюз])

    G --> UC1(Переглядати каталог)
    G --> UC2(Шукати і фільтрувати)
    G --> UC3(Реєстрація / вхід)
    U --> UC4(Дивитись відео з рекламою)
    U --> UC5(Керувати профілем)
    U --> UC6(Додавати у Вибране)
    U --> UC7(Бачити рекомендації)
    U --> UC8(Оформити преміум-підписку)
    P --> UC9(Дивитись без реклами у вищій якості)
    UC8 --> PG
    A --> UC10(CRUD фільмів, серіалів, жанрів)
    A --> UC11(Завантажити відео, запустити HLS-конвертацію)
    A --> UC12(Керувати користувачами і підписками)
    A --> UC13(Переглядати звіти)
```

Примітка: Користувач наслідує можливості Гостя, Преміум-користувач — Користувача.

## 2. Модель даних (ER)

```mermaid
erDiagram
    USER ||--o| PROFILE : has
    USER ||--o{ SUBSCRIPTION : owns
    USER ||--o{ PAYMENT : makes
    USER ||--o{ FAVORITE : saves
    USER ||--o{ WATCH_HISTORY : watches
    PLAN ||--o{ SUBSCRIPTION : defines
    PLAN ||--o{ PAYMENT : paid_for
    TITLE ||--o{ FAVORITE : in
    TITLE }o--o{ GENRE : tagged
    TITLE ||--o{ SEASON : has
    SEASON ||--o{ EPISODE : has
    TITLE ||--o| VIDEO_ASSET : "movie video"
    EPISODE ||--o| VIDEO_ASSET : "episode video"
    TITLE ||--o{ WATCH_HISTORY : in
    EPISODE ||--o{ WATCH_HISTORY : in

    USER { int id string email string password_hash string role datetime created_at }
    PROFILE { int user_id string display_name string avatar_url string country }
    PLAN { int id string code string name decimal price_month bool ads_enabled int max_height }
    SUBSCRIPTION { int id int user_id int plan_id string status datetime started_at datetime expires_at }
    PAYMENT { int id int user_id int plan_id decimal amount string status string provider string external_id datetime created_at }
    TITLE { int id string kind string name text description int year string country float rating string poster_url }
    GENRE { int id string name }
    SEASON { int id int title_id int number }
    EPISODE { int id int season_id int number string name }
    VIDEO_ASSET { int id string hls_path string status int title_id int episode_id }
    FAVORITE { int user_id int title_id datetime added_at }
    WATCH_HISTORY { int id int user_id int title_id int episode_id int progress_sec bool finished datetime last_watched }
```

Плани створюються сідом (`python -m app.seed`): `free` (реклама, до 720p, 0 грн) і `premium` (без реклами, до 1080p,
99 грн/міс). Користувач без активної `SUBSCRIPTION` вважається на плані `free`, тому окремий запис підписки для Free
не створюється. Сід також створює адміністратора з `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

`python -m app.seed --demo` додатково завантажує демо-каталог (`app/demo_data.py`): 12 жанрів, 25 фільмів і 6 серіалів
із сезонами та епізодами. Повторний запуск не створює дублікатів: тайтл шукається за (kind, name, year), довідкові
поля відновлюються, а постер, перейменовані епізоди й додані адміністратором сезони зберігаються.

Цілісність каталогу: номер сезону унікальний у межах тайтлу, номер епізоду — у межах сезону (унікальні обмеження в БД
плюс перевірка в `AdminCatalogService` з кодом 409). Сезони додаються лише до серіалів. Видалення тайтлу каскадно
прибирає сезони, епізоди, зв'язки з жанрами, відео, «Вибране», історію переглядів і файл постера. Постери зберігаються
в `media/posters/` через абстракцію `FileStorage` (`LocalMediaStorage`) і роздаються за адресою `/media/...`.

## 3. Патерни і взаємодія

```
Router ──> PlaybackService ──> PlaybackProxy ──> (RealPlayback) HLS manifest
                                   │  перевіряє SubscriptionPlan (Factory Method → PlanPolicy)
                                   └─ повертає: дозволені якості, прапорець реклами
Router ──> CatalogService (Director) ──> TitleQueryBuilder ──build()──> TitleQuery ──> TitleRepository
Router ──> RecommendationService ──> RecommendationStrategy (Genre | Popularity | Hybrid)
Router ──> BillingService ──> PaymentGateway (Adapter → MockGateway: success/pending/failed)
                    │ успіх
                    └─> EventBus.publish(PaymentSucceeded) ──> SubscriptionActivator (Observer)
PlaybackService ──> EventBus.publish(WatchFinished) ──> StatsUpdater (Observer)
Reports: ReportGenerator (Template Method) ──> PopularTitles | UserActivity | Revenue
```

Як патерни працюють разом: проксі отримує політику від фабрики, платіж через адаптер породжує подію, яку обробляють
спостерігачі (активація підписки), після чого проксі вже пускає користувача без реклами.

GRASP: Controller (роутери), Information Expert (політика плану знає про рекламу і якість), Low Coupling / High Cohesion
(шари), Polymorphism (стратегії, шлюзи), Pure Fabrication (EventBus), Protected Variations (інтерфейс шлюзу).

### 3.1 Builder — пошук і фільтри каталогу

Файл: `backend/app/patterns/title_query_builder.py`. Тести: `backend/tests/test_title_query_builder.py`.

**Проблема.** `GET /api/titles` має десять необов'язкових параметрів: текст, жанри, роки «від» і «до», країна, тип,
мінімальний рейтинг, сортування, напрям, сторінка. Будь-яка їх комбінація допустима. Якщо збирати SQL-запит
умовами `if` у роутері чи репозиторії, виходить довгий метод, у якому змішано HTTP, бізнес-правила і ORM. Сигнатура
`search(q, genres, year_from, year_to, ...)` розростається, а кожен новий фільтр вимагає змін у кількох шарах.

**Рішення.** Запит будується покроково: кожен крок додає одну умову і повертає сам білдер (fluent-інтерфейс), а
`build()` віддає готовий продукт — пару запитів «записи сторінки» і «загальна кількість» з однаковими умовами.

```mermaid
classDiagram
    direction LR
    class CatalogService {
        <<Director>>
        +build_query(filters: TitleFilters) TitleQuery
        +search(filters: TitleFilters) TitlePage
    }
    class TitleQueryBuilder {
        <<Builder>>
        -conditions: list
        -order: list
        -page: int
        -page_size: int
        +with_text(text) TitleQueryBuilder
        +with_genres(genre_ids) TitleQueryBuilder
        +with_year_range(year_from, year_to) TitleQueryBuilder
        +with_country(country) TitleQueryBuilder
        +with_kind(kind) TitleQueryBuilder
        +with_min_rating(min_rating) TitleQueryBuilder
        +sort_by(field, order) TitleQueryBuilder
        +paginate(page, page_size) TitleQueryBuilder
        +build() TitleQuery
    }
    class TitleQuery {
        <<Product>>
        +items: Select
        +count: Select
        +page: int
        +page_size: int
    }
    class TitleReader {
        <<interface>>
        +search(query: TitleQuery) tuple
    }
    class TitleRepository {
        +search(query: TitleQuery) tuple
    }
    CatalogService ..> TitleQueryBuilder : керує кроками
    TitleQueryBuilder ..> TitleQuery : створює
    CatalogService --> TitleReader
    TitleRepository ..|> TitleReader
    TitleRepository ..> TitleQuery : виконує
```

| Роль GoF | Клас | Відповідальність |
|---|---|---|
| Builder | `TitleQueryBuilder` | знає, як кожен фільтр перетворюється на SQL-умову |
| Director | `CatalogService.build_query` | знає, які кроки викликати для `TitleFilters` |
| Product | `TitleQuery` | незмінний результат: запит сторінки, count-запит, межі сторінки |
| Client | `TitleRepository.search` | виконує продукт, не знаючи, як його зібрано |

**Використання в `CatalogService`.**

```python
query = (
    TitleQueryBuilder()
    .with_text(filters.q)
    .with_genres(filters.genre)
    .with_year_range(filters.year_from, filters.year_to)
    .with_country(filters.country)
    .with_kind(filters.kind)
    .with_min_rating(filters.min_rating)
    .sort_by(filters.sort, filters.order)
    .paginate(filters.page, filters.page_size)
    .build()
)
items, total = self.titles.search(query)
```

Потік: роутер валідує параметри в `TitleFilters` (Pydantic, 422) → `CatalogService` як директор збирає `TitleQuery` →
репозиторій через абстракцію `TitleReader` виконує обидва запити → сервіс повертає `TitlePage {items, total, page, page_size}`.

Ключові рішення всередині білдера:
- незаданий параметр (`None`, порожній рядок, порожній список) не додає умови, тому директор викликає всі кроки без `if`;
- жанри з'єднуються логікою «будь-який із» через підзапит `title_id IN (...)`, тому немає дублікатів рядків, а `total`
  рахується правильно без `DISTINCT`;
- текст шукається через `ILIKE` у назві й описі, символи `%` і `_` екрануються;
- сортування стабільне: до будь-якого поля додається `id`, щоб сторінки не перекривались; для кожного поля є
  природний напрям за замовчуванням (рейтинг, рік, популярність — за спаданням, назва — за зростанням);
- білдер сам перевіряє інваріанти продукту (`page_size ≤ 50`, `year_from ≤ year_to`, рейтинг 0–10) і кидає 422, тож
  некоректний запит неможливо зібрати незалежно від того, хто викликає білдер.

**Чому патерн доречний.**
- Об'єкт (запит) складний, має багато необов'язкових частин і будується покроково — це класичний випадок Builder.
- SRP: SQL-логіка фільтрів зосереджена в одному класі; роутер працює лише з HTTP, сервіс — лише з порядком кроків,
  репозиторій — лише з виконанням.
- OCP: новий фільтр — це новий метод білдера і один рядок у директорі; репозиторій і роутер-контракт не змінюються.
- DIP: `CatalogService` залежить від протоколу `TitleReader`, а не від SQLAlchemy-репозиторію.
- Тестованість: кожен крок і їхні комбінації перевіряються окремо (44 unit-тести), без HTTP-шару.
- Повторне використання: той самий білдер знадобиться для рекомендацій (вибірка кандидатів за жанрами й рейтингом)
  та адмін-списків.

Відмінність від канонічної схеми GoF: абстрактного інтерфейсу Builder немає, бо існує одне подання продукту
(SQLAlchemy `Select`). Якщо з'явиться інше джерело пошуку (наприклад, повнотекстовий індекс), достатньо виділити
інтерфейс із тими самими кроками — директор `CatalogService` при цьому не зміниться.

## 4. Оплата (mock)

1. `POST /billing/checkout {plan_code}` → створює `Payment(status=created)`, повертає `payment_id`.
2. UI показує сторінку оплати з вибором результату: **success / pending / failed**.
3. `POST /billing/payments/{id}/mock-result {outcome}` → MockGateway повертає результат:
   - success → `Payment=success`, подія `PaymentSucceeded`, підписка Premium активна на 30 днів;
   - pending → `Payment=pending`, підписка не змінюється; адмін або користувач може пізніше «підтвердити» (повторний виклик);
   - failed → `Payment=failed`, підписка не змінюється.

## 5. HLS

Для кожного відео: `ffmpeg` → `media/<asset_id>/{360p,720p,1080p}/index.m3u8` + `master.m3u8`.
Бекенд віддає `master.m3u8` через проксі: Free бачить до 720p і рекламу перед фільмом, Premium — до 1080p без реклами.

## 6. План на 7 днів

| День | Дата | Результат |
|---|---|---|
| 1 | сб 21.11 | Репозиторій, compose, моделі, Alembic, auth (реєстрація/вхід/JWT), каркас React |
| 2 | нд 22.11 | Каталог, пошук/фільтри (Builder), адмін CRUD для фільмів/жанрів |
| 3 | пн 23.11 | ffmpeg → HLS, плеєр, Playback Proxy, Вибране, історія переглядів |
| 4 | вт 24.11 | Плани, Factory Method, оплата (Adapter + mock UI), EventBus (Observer) |
| 5 | ср 25.11 | Рекомендації (Strategy), звіти (Template Method), адмін-дашборд |
| 6 | чт 26.11 | Тести, полірування UI, UML (Use Case, класи з кольорами патернів), скріни |
| 7 | пт 27.11 | Звіт, README, фінальний прогін розгортання з нуля, запас часу |
