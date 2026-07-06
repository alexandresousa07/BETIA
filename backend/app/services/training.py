from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.training.data_collector import HistoricalDataCollector
from app.ml.training.trainer import HistoricalTrainer
from app.integrations.league_mapping import DEFAULT_TRAINING_LEAGUES
from app.repositories.competition import CompetitionRepository


class TrainingService:
    def __init__(self, session: AsyncSession | None = None):
        self.session = session
        self.collector = HistoricalDataCollector()
        self.trainer = HistoricalTrainer()

    async def _resolve_league_ids(self, league_ids: list[int] | None) -> list[int]:
        if league_ids:
            return league_ids
        if self.session:
            ids = await CompetitionRepository(self.session).get_active_league_external_ids()
            if ids:
                return ids[:20]
        return DEFAULT_TRAINING_LEAGUES

    async def collect_data(
        self,
        league_ids: list[int] | None = None,
        season: int | None = None,
        max_pages: int = 3,
    ) -> dict:
        resolved = await self._resolve_league_ids(league_ids)
        samples = await self.collector.collect_multiple_leagues(
            league_ids=resolved,
            season=season,
            max_pages=max_pages,
        )
        return {
            "samples_collected": len(samples),
            "leagues": resolved,
            "season": season,
        }

    async def run_full_pipeline(
        self,
        league_ids: list[int] | None = None,
        season: int | None = None,
        max_pages: int = 3,
    ) -> dict:
        resolved = await self._resolve_league_ids(league_ids)
        samples = await self.collector.collect_multiple_leagues(
            league_ids=resolved,
            season=season,
            max_pages=max_pages,
        )

        if len(samples) < 50:
            return {
                "success": False,
                "message": f"Dados insuficientes: {len(samples)} amostras (mínimo 50)",
                "samples_collected": len(samples),
            }

        metrics = self.trainer.train(samples)
        return {
            "success": True,
            "samples_collected": len(samples),
            "markets_trained": list(metrics.get("markets", {}).keys()),
            "metrics": metrics,
        }

    def get_training_status(self) -> dict:
        registry = HistoricalTrainer.load_registry()
        if not registry:
            return {"status": "not_trained", "markets": []}

        markets_summary = {}
        for market, data in registry.get("markets", {}).items():
            best_model = None
            best_auc = 0
            for model_name, model_data in data.get("models", {}).items():
                auc = model_data.get("roc_auc", 0)
                if auc > best_auc:
                    best_auc = auc
                    best_model = model_name
            markets_summary[market] = {"best_model": best_model, "roc_auc": best_auc}

        return {
            "status": "trained",
            "trained_at": registry.get("trained_at"),
            "total_samples": registry.get("total_samples"),
            "markets": markets_summary,
        }
