import random
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.security import hash_password
from app.models import (
    Episode, Favorite, Payment, PaymentStatus, Plan, PlanCode, Profile, Role, Season, Subscription, SubscriptionStatus,
    Title, User, VideoStatus, WatchHistory,
)
from app.repositories.title_stats_repository import TitleStatsRepository
from app.services.ports import StatsTotals
from app.services.title_stats import TitleStatsService

DEMO_PASSWORD = "demo12345"
DEMO_USERS = 40
DEMO_DAYS = 90
DEMO_SEED = 17
EMAIL_TEMPLATE = "demo.user{:02d}@example.com"
PREMIUM_DAYS = 30
PAYER_EVERY = 3

FIRST_NAMES = (
    "Олена", "Андрій", "Марія", "Тарас", "Ірина", "Богдан", "Софія", "Дмитро", "Наталія", "Остап",
    "Юлія", "Максим", "Катерина", "Василь", "Оксана", "Ярослав", "Дарина", "Роман", "Христина", "Назар",
)
LAST_NAMES = (
    "Коваленко", "Шевчук", "Бондар", "Мельник", "Ткачук", "Кравець", "Олійник", "Лисенко", "Гнатюк", "Савчук",
)
GENRE_POPULARITY = {
    "Драма": 5, "Фантастика": 5, "Комедія": 4, "Трилер": 4, "Бойовик": 3, "Кримінал": 3,
    "Пригоди": 3, "Детектив": 2, "Мелодрама": 2, "Анімація": 2, "Історичний": 1, "Жахи": 1,
}
MOVIE_MINUTES = (95, 150)
EPISODE_MINUTES = (40, 58)
MIDDAY_UTC = (8, 20)


def _display_name(index: int) -> str:
    first = FIRST_NAMES[index % len(FIRST_NAMES)]
    last = LAST_NAMES[(index + index // len(FIRST_NAMES)) % len(LAST_NAMES)]
    return f"{first} {last}"


@dataclass(frozen=True)
class DemoActivitySummary:
    users: int
    history: int
    favorites: int
    payments: dict[str, int]
    active_premium: int
    stats: StatsTotals


@dataclass
class _Viewer:
    user: User
    registered_at: datetime
    genres: tuple[str, ...]


class _Generator:
    def __init__(self, session: Session, now: datetime, rng: random.Random) -> None:
        self.session = session
        self.now = now
        self.rng = rng
        self.titles = self._load_titles()
        self.by_genre: dict[str, list[Title]] = {}
        for title in self.titles:
            for genre in title.genres:
                self.by_genre.setdefault(genre.name, []).append(title)
        self.history: list[WatchHistory] = []
        self.favorites: list[Favorite] = []
        self.payments: list[Payment] = []
        self.subscriptions: list[Subscription] = []

    def _load_titles(self) -> list[Title]:
        titles = list(self.session.scalars(
            select(Title)
            .options(
                selectinload(Title.video),
                selectinload(Title.seasons).selectinload(Season.episodes).selectinload(Episode.video),
            )
            .order_by(Title.id)
        ))
        if not titles:
            raise RuntimeError("Demo activity needs a catalog; run `python -m app.seed --demo` first")
        return titles

    def _between(self, start: datetime, end: datetime) -> datetime:
        end = min(end, self.now)
        if end <= start:
            return start
        return start + timedelta(seconds=self.rng.uniform(0, (end - start).total_seconds()))

    def users(self, password_hash: str) -> list[_Viewer]:
        first_day = self.now.date() - timedelta(days=DEMO_DAYS)
        genres = [g for g in GENRE_POPULARITY if g in self.by_genre]
        weights = [GENRE_POPULARITY[g] for g in genres]
        viewers = []
        for index in range(DEMO_USERS):
            day = first_day + timedelta(days=round(index * DEMO_DAYS / (DEMO_USERS - 1)))
            registered_at = datetime.combine(day, time(self.rng.randint(6, 10), self.rng.randint(0, 59)), UTC)
            registered_at = min(registered_at, self.now - timedelta(minutes=30))
            liked = tuple(dict.fromkeys(self.rng.choices(genres, weights, k=self.rng.randint(1, 2))))
            user = User(
                email=EMAIL_TEMPLATE.format(index + 1),
                password_hash=password_hash,
                role=Role.USER.value,
                created_at=registered_at,
                profile=Profile(
                    display_name=_display_name(index),
                    country="Україна",
                ),
            )
            viewers.append(_Viewer(user, registered_at, liked))
        self.session.add_all(v.user for v in viewers)
        self.session.flush()
        return viewers

    def _pick_titles(self, viewer: _Viewer, count: int) -> list[Title]:
        liked = list(dict.fromkeys(t for g in viewer.genres for t in self.by_genre.get(g, [])))
        chosen: list[Title] = []
        while len(chosen) < min(count, len(self.titles)):
            pool = liked if liked and self.rng.random() < 0.7 else self.titles
            candidates = [t for t in pool if t not in chosen] or [t for t in self.titles if t not in chosen]
            chosen.append(self.rng.choice(candidates))
        return chosen

    def _duration(self, video_duration: int | None, status: str | None, minutes: tuple[int, int]) -> int:
        if video_duration and status == VideoStatus.READY:
            return video_duration
        return self.rng.randint(*minutes) * 60

    def _entry(self, viewer: _Viewer, title: Title, episode: Episode | None, at: datetime, finished: bool) -> None:
        video = episode.video if episode is not None else title.video
        duration = self._duration(
            video.duration_sec if video else None,
            video.status if video else None,
            EPISODE_MINUTES if episode is not None else MOVIE_MINUTES,
        )
        progress = duration if finished else max(30, int(duration * self.rng.uniform(0.1, 0.9)))
        self.history.append(WatchHistory(
            user_id=viewer.user.id,
            title_id=title.id,
            episode_id=episode.id if episode else None,
            progress_sec=progress,
            finished=finished,
            last_watched=at,
        ))

    def watch(self, viewer: _Viewer) -> None:
        tenure_days = (self.now - viewer.registered_at).days
        count = min(self.rng.randint(5, 20), 3 + tenure_days // 3)
        for title in self._pick_titles(viewer, count):
            started = self._between(viewer.registered_at, self.now)
            episodes = [e for s in title.seasons for e in s.episodes]
            if not episodes:
                self._entry(viewer, title, None, started, self.rng.random() < 0.6)
                continue
            watched = episodes[:self.rng.randint(1, min(len(episodes), 6))]
            at = started
            for number, episode in enumerate(watched, start=1):
                last = number == len(watched)
                self._entry(viewer, title, episode, at, not last or self.rng.random() < 0.6)
                at = min(at + timedelta(hours=self.rng.uniform(2, 30)), self.now)

    def favorite(self, viewer: _Viewer) -> None:
        liked = list(dict.fromkeys(t for g in viewer.genres for t in self.by_genre.get(g, [])))
        for title in self.rng.sample(liked, min(len(liked), self.rng.randint(1, 4))):
            self.favorites.append(Favorite(
                user_id=viewer.user.id, title_id=title.id, added_at=self._between(viewer.registered_at, self.now)
            ))

    def _payment(self, viewer: _Viewer, plan: Plan, status: PaymentStatus, created_at: datetime) -> Payment:
        number = len(self.payments) + 1
        payment = Payment(
            user_id=viewer.user.id,
            plan_id=plan.id,
            amount=plan.price_month,
            status=status.value,
            provider="mock",
            external_id=f"demo_inv_{number:04d}",
            created_at=created_at,
            paid_at=created_at + timedelta(minutes=self.rng.randint(1, 5)) if status is PaymentStatus.SUCCESS else None,
        )
        self.payments.append(payment)
        return payment

    def pay(self, viewer: _Viewer, plan: Plan, index: int) -> None:
        if self.rng.random() < 0.25:
            self._payment(viewer, plan, PaymentStatus.FAILED, self._between(viewer.registered_at, self.now))
        if index % PAYER_EVERY and self.rng.random() >= 0.05:
            if self.rng.random() < 0.15:
                self._payment(viewer, plan, PaymentStatus.PENDING,
                              self._between(self.now - timedelta(days=7), self.now))
            return
        first = viewer.registered_at + timedelta(days=self.rng.uniform(0, 5), hours=self.rng.uniform(1, 12))
        renewals = 0
        while first + timedelta(days=PREMIUM_DAYS * renewals) < self.now and (not renewals or self.rng.random() < 0.8):
            self._payment(viewer, plan, PaymentStatus.SUCCESS, first + timedelta(days=PREMIUM_DAYS * renewals))
            renewals += 1
        if not renewals:
            return
        expires_at = first + timedelta(days=PREMIUM_DAYS * renewals)
        self.subscriptions.append(Subscription(
            user_id=viewer.user.id,
            plan_id=plan.id,
            status=(SubscriptionStatus.ACTIVE if expires_at > self.now else SubscriptionStatus.EXPIRED).value,
            started_at=first,
            expires_at=expires_at,
        ))

    @staticmethod
    def _midday(entry: WatchHistory) -> bool:
        return MIDDAY_UTC[0] <= entry.last_watched.hour < MIDDAY_UTC[1]

    def fill_quiet_days(self, viewers: Sequence[_Viewer]) -> None:
        first_day = self.now.date() - timedelta(days=DEMO_DAYS)
        covered = Counter(e.last_watched.date() for e in self.history if self._midday(e))
        for offset in range(DEMO_DAYS):
            day = first_day + timedelta(days=offset)
            if covered[day]:
                continue
            noon = datetime.combine(day, time(12), UTC)
            eligible = {v.user.id for v in viewers if v.registered_at <= noon}
            movable = [
                e for e in self.history
                if e.user_id in eligible and (not self._midday(e) or covered[e.last_watched.date()] > 1)
            ]
            entry = self.rng.choice(movable)
            if self._midday(entry):
                covered[entry.last_watched.date()] -= 1
            entry.last_watched = noon + timedelta(minutes=self.rng.randint(0, 359))
            covered[day] += 1

    def ensure_statuses(self, viewers: Sequence[_Viewer], plan: Plan) -> None:
        present = {p.status for p in self.payments}
        recent = self.now - timedelta(days=3)
        if PaymentStatus.PENDING.value not in present:
            self._payment(viewers[-1], plan, PaymentStatus.PENDING, recent)
        if PaymentStatus.FAILED.value not in present:
            self._payment(viewers[-2], plan, PaymentStatus.FAILED, recent)


def demo_emails() -> list[str]:
    return [EMAIL_TEMPLATE.format(number) for number in range(1, DEMO_USERS + 1)]


def delete_demo_users(session: Session) -> None:
    session.execute(delete(User).where(User.email.in_(demo_emails())), execution_options={"synchronize_session": False})


def seed_demo_activity(session: Session, now: datetime | None = None, rng_seed: int = DEMO_SEED) -> DemoActivitySummary:
    now = now or datetime.now(UTC)
    plan = session.scalar(select(Plan).where(Plan.code == PlanCode.PREMIUM.value))
    if plan is None:
        raise RuntimeError("Plans are not seeded; run `python -m app.seed` first")
    delete_demo_users(session)
    generator = _Generator(session, now, random.Random(rng_seed))
    viewers = generator.users(hash_password(DEMO_PASSWORD))
    for index, viewer in enumerate(viewers):
        generator.watch(viewer)
        generator.favorite(viewer)
        generator.pay(viewer, plan, index)
    generator.fill_quiet_days(viewers)
    generator.ensure_statuses(viewers, plan)
    session.add_all([*generator.history, *generator.favorites, *generator.payments, *generator.subscriptions])
    session.flush()
    stats = TitleStatsService(TitleStatsRepository(session)).rebuild()
    return DemoActivitySummary(
        users=len(viewers),
        history=len(generator.history),
        favorites=len(generator.favorites),
        payments=dict(Counter(p.status for p in generator.payments)),
        active_premium=sum(s.status == SubscriptionStatus.ACTIVE.value for s in generator.subscriptions),
        stats=stats,
    )
