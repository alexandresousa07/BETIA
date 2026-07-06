import asyncio

from app.workers.celery_app import celery_app


def run_async(coro_fn):
    async def _wrapper():
        try:
            return await coro_fn()
        finally:
            from app.database.session import engine
            await engine.dispose()

    return asyncio.run(_wrapper())


@celery_app.task(name="app.workers.tasks.sync_live_matches")
def sync_live_matches():
    async def _sync():
        from app.database.session import AsyncSessionLocal
        from app.services.match import MatchService

        async with AsyncSessionLocal() as session:
            service = MatchService(session)
            matches = await service.sync_live_matches()
            await session.commit()
            return len(matches)

    return run_async(_sync)


@celery_app.task(name="app.workers.tasks.update_monitored_matches")
def update_monitored_matches():
    async def _update():
        from app.database.session import AsyncSessionLocal
        from app.repositories.domain import MatchRepository
        from app.services.match import MatchService

        async with AsyncSessionLocal() as session:
            repo = MatchRepository(session)
            service = MatchService(session)
            matches = await repo.get_monitored_matches()
            updated = 0
            for match in matches:
                await service.update_match_live_data(match)
                updated += 1
            await session.commit()
            return updated

    return run_async(_update)


@celery_app.task(name="app.workers.tasks.analyze_match")
def analyze_match(match_id: int):
    async def _analyze():
        from app.database.session import AsyncSessionLocal
        from app.repositories.domain import MatchRepository
        from app.services.match import MatchService

        async with AsyncSessionLocal() as session:
            repo = MatchRepository(session)
            service = MatchService(session)
            match = await repo.get_by_id(match_id)
            if match:
                result = await service.update_match_live_data(match)
                await session.commit()
                return result
            return None

    return run_async(_analyze)


@celery_app.task(name="app.workers.tasks.match_odds")
def match_odds():
    async def _match():
        from app.database.session import AsyncSessionLocal
        from app.services.odds import OddsService

        async with AsyncSessionLocal() as session:
            result = await OddsService(session).match_all_live()
            await session.commit()
            return result

    return run_async(_match)


@celery_app.task(name="app.workers.tasks.sync_leagues")
def sync_leagues():
    async def _sync():
        from app.database.session import AsyncSessionLocal
        from app.services.league_sync import LeagueSyncService

        async with AsyncSessionLocal() as session:
            result = await LeagueSyncService(session).sync_all_leagues()
            await session.commit()
            return result

    return run_async(_sync)


@celery_app.task(name="app.workers.tasks.train_historical_models")
def train_historical_models(season: int | None = None, max_pages: int = 3):
    async def _train():
        from app.services.training import TrainingService

        service = TrainingService()
        return await service.run_full_pipeline(season=season, max_pages=max_pages)

    return run_async(_train)
