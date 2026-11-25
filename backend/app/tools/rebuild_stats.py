import argparse
from collections.abc import Sequence

from app.core.db import SessionLocal
from app.repositories.title_stats_repository import TitleStatsRepository
from app.services.title_stats import TitleStatsService


def main(argv: Sequence[str] | None = None) -> int:
    argparse.ArgumentParser(
        prog="python -m app.tools.rebuild_stats", description="Recalculate title_stats from watch_history."
    ).parse_args(argv)

    with SessionLocal() as session, session.begin():
        totals = TitleStatsService(TitleStatsRepository(session)).rebuild()
    print(f"Rebuilt stats: {totals.titles} titles, {totals.viewers} viewers, {totals.completions} completions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
