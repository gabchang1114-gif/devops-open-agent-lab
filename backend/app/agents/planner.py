"""Agent planner placeholder.

Future responsibility: Determine Next Action
"""


class AgentPlanner:
    """Placeholder planner agent for orchestrating investigation workflows."""

    async def plan(self, context: dict) -> list[dict]:
        raise NotImplementedError("Agent planning is not implemented yet.")

    async def determine_next_action(self, state: dict) -> dict:
        raise NotImplementedError("Agent planning is not implemented yet.")
