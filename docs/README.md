# Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — DevOps Open Agent platform structure, shared components, and agent conventions

## Architecture diagrams (downloadable)

| File | Format | Description |
|------|--------|-------------|
| [architecture-diagram.html](./architecture-diagram.html) | HTML | Open in a browser; use Print → Save as PDF |
| [diagrams/system-context.png](./diagrams/system-context.png) | PNG | System context diagram |
| [diagrams/system-context.svg](./diagrams/system-context.svg) | SVG | System context (vector) |
| [diagrams/application-layers.png](./diagrams/application-layers.png) | PNG | Application layers diagram |
| [diagrams/application-layers.svg](./diagrams/application-layers.svg) | SVG | Application layers (vector) |
| [application-request-flow.canvas.tsx](./application-request-flow.canvas.tsx) | Canvas source | Application request flow only (matches interactive canvas) |
| [devops-open-agent-architecture.canvas.tsx](./devops-open-agent-architecture.canvas.tsx) | Canvas source | Full architecture canvas source |
| [devops-open-agent-architecture.html](./devops-open-agent-architecture.html) | HTML | Static export of application request flow — open in browser or Print → PDF |
| [diagrams/application-request-flow.svg](./diagrams/application-request-flow.svg) | SVG | Application request flow (vector) |
| [diagrams/application-request-flow.png](./diagrams/application-request-flow.png) | PNG | Application request flow |
| [../img/aws-services-diagram.png](../img/aws-services-diagram.png) | PNG | AWS DevOps Agent → supported services |
| [../img/aws-services-diagram.svg](../img/aws-services-diagram.svg) | SVG | AWS services architecture (vector) |
| [../img/llm-provider-diagram.png](../img/llm-provider-diagram.png) | PNG | Shared LLM provider architecture |

**Regenerate AWS / LLM diagrams:**

```bash
python3 scripts/build_aws_services_diagram.py
python3 scripts/build_llm_diagram.py
```

**Regenerate PNG/SVG from Mermaid:**

```bash
cd docs/diagrams
npx @mermaid-js/mermaid-cli -i system-context.mmd -o system-context.png
npx @mermaid-js/mermaid-cli -i application-layers.mmd -o application-layers.png
```
