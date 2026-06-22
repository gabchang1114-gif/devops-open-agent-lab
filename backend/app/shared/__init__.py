"""Shared platform package.

Target layout (migration in progress):
- shared/llm/          -> app.ai (LLM providers, factory)
- shared/database/     -> app.storage, app.db
- shared/topology/     -> app.graph (framework) + agent modules
- shared/memory/       -> app.memory (future)
- shared/observability/ -> app.observability (future)
"""
