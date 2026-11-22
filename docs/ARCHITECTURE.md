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
Router ──> CatalogService ──> TitleQueryBuilder ──> TitleRepository
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
