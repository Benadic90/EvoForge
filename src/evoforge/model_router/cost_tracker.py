
import structlog

logger = structlog.get_logger(__name__)

class CostTracker:
    def __init__(self, daily_budget_usd: float = 5.00):
        self.daily_budget_usd = daily_budget_usd
        self.spent_today_usd = 0.0
        self.per_provider_spent: dict[str, float] = {}
        self.per_agent_spent: dict[str, float] = {}
        self.per_project_spent: dict[str, float] = {}

    def record_cost(self, cost_usd: float, provider: str, agent: str = "unknown", project: str = "unknown"):
        """Records an API cost against the daily budget."""
        if cost_usd <= 0:
            return

        self.spent_today_usd += cost_usd
        
        self.per_provider_spent[provider] = self.per_provider_spent.get(provider, 0.0) + cost_usd
        self.per_agent_spent[agent] = self.per_agent_spent.get(agent, 0.0) + cost_usd
        self.per_project_spent[project] = self.per_project_spent.get(project, 0.0) + cost_usd
        
        logger.debug("cost_recorded", amount=cost_usd, total_spent=self.spent_today_usd, provider=provider)

    def can_afford(self, estimated_cost: float = 0.10) -> bool:
        """Checks if there is enough budget remaining for an operation."""
        remaining = self.daily_budget_usd - self.spent_today_usd
        if remaining < estimated_cost:
            logger.warning("budget_exhausted", spent=self.spent_today_usd, budget=self.daily_budget_usd)
            return False
        return True
        
    def reset_daily(self):
        """Resets the cost trackers for a new day."""
        self.spent_today_usd = 0.0
        self.per_provider_spent = {}
        self.per_agent_spent = {}
        self.per_project_spent = {}
        logger.info("cost_tracker_reset")
