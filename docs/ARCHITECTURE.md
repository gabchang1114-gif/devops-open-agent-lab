# DevOps Open Agent — Platform Architecture

Open Source · Self Hostable · Cloud Agnostic · Vendor Neutral

**Tagline:** Open Source AI-Powered DevOps Troubleshooting Platform

## Product Structure

```
DevOps Open Agent
├── Kubernetes Debugging Agent   (implemented)
└── AWS DevOps Agent             (planned)
```

Future agents: Docker, Linux, Terraform, CI/CD, Azure, GCP.

## Navigation

- **Platform level:** agent switcher (Kubernetes, AWS, …)
- **Agent level:** agent-specific tabs (e.g. Investigate, Investigations, Topology)

Frontend config: `frontend/lib/platform.ts`

## Shared Platform (reuse across agents)

| Layer | Current location | Target |
|-------|------------------|--------|
| LLM providers | `backend/app/ai/` | `shared/llm/` |
| Database | `backend/app/storage/`, `app/db/` | `shared/database/` |
| Topology framework | `backend/app/graph/` | `shared/topology/` |
| Memory | `backend/app/memory/` (stub) | `shared/memory/` |
| Observability | `backend/app/observability/` (stub) | `shared/observability/` |
| Auth | `backend/app/auth/`, `app/db/` | shared |
| Agent framework | `backend/app/agents/` (stub) | shared |

## LLM Support

All agents use the same provider layer:

```env
LLM_PROVIDER=openai|anthropic|ollama|openrouter
```

Implementation: `backend/app/ai/llm_factory.py`

## AI Pipeline (every agent)

```
Evidence Collection → Context Builder → Prompt Builder → LLM Provider
→ Diagnosis → Confidence Engine → Recommended Actions
```

## Agent-Specific Code

Keep isolated per agent:

- Discovery / investigation engines
- Domain models and prompts
- RCA workflows
- Topology relationship builders

| Agent | Backend | Frontend |
|-------|---------|----------|
| Kubernetes | `backend/app/kubernetes/`, K8s APIs | `/`, `/investigations`, `/topology` |
| AWS | `backend/app/modules/aws/` (investigation engine) | `/aws` |

## Investigation History

Shared history includes:

- Investigation ID
- **agent_type** (`kubernetes`, `aws`, …)
- Timestamp, root cause, confidence, status

## Database

- Investigations: SQLite (phase 1), abstraction in `storage/`
- Auth: PostgreSQL

## Security

- Never expose API keys, secrets, or K8s secret values
- Never auto-execute remediation — human approval required

## Constraints

No vendor lock-in, proprietary dependencies, or closed-source services.

## Adding a New Agent

1. Add agent to `frontend/lib/platform.ts`
2. Create `backend/app/modules/<agent>/` with router, services, models
3. Register API router in `backend/app/main.py`
4. Implement discovery → investigation → topology → AI using shared `app/ai/`
5. Store investigations with `agent_type=<agent>`
