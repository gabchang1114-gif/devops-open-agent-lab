High-Level Architecture
                               ┌──────────────┐
                               │     USER     │
                               └──────┬───────┘
                                      │
                                      ▼
                            ┌───────────────────┐
                            │  REACT FRONTEND   │
                            │ Cloud Cost Detector│
                            └────────┬──────────┘
                                     │
                                     ▼
                            ┌───────────────────┐
                            │  FASTAPI BACKEND  │
                            │                   │
                            │ Authentication    │
                            │ Analysis Engine   │
                            │ Report Generator  │
                            └────┬─────┬─────┬──┘
                                 │     │     │
                                 │     │     │
                                 ▼     ▼     ▼

                   ┌─────────────────────────────┐
                   │ AWS Discovery Engine        │
                   │                             │
                   │ EC2                         │
                   │ EBS                         │
                   │ ALB/NLB                     │
                   │ VPC                         │
                   │ NAT Gateway                 │
                   │ Elastic IP                  │
                   │ RDS (Future)                │
                   └──────────────┬──────────────┘
                                  │
                                  ▼

                   ┌─────────────────────────────┐
                   │ AWS Cost Analysis Engine    │
                   │                             │
                   │ Cost Explorer               │
                   │ Trusted Advisor             │
                   │ Compute Optimizer           │
                   │ CloudWatch Metrics          │
                   └──────────────┬──────────────┘
                                  │
                                  ▼

                   ┌─────────────────────────────┐
                   │ Topology Graph Engine       │
                   │                             │
                   │ Resource Relationships      │
                   │ Dependency Mapping          │
                   │ Cost Attribution            │
                   └──────────────┬──────────────┘
                                  │
                                  ▼

                   ┌─────────────────────────────┐
                   │ AI Cost Optimization Agent  │
                   │                             │
                   │ OpenAI                      │
                   │ Anthropic                   │
                   │ Ollama                      │
                   │ OpenRouter                  │
                   └──────────────┬──────────────┘
                                  │
                                  ▼

                   ┌─────────────────────────────┐
                   │ Investigation Database      │
                   │                             │
                   │ Users                       │
                   │ Analyses                    │
                   │ Findings                    │
                   │ Recommendations             │
                   └──────────────┬──────────────┘
                                  │
                                  ▼

                            ┌───────────────────┐
                            │   REACT UI        │
                            │                   │
                            │ Cost Report       │
                            │ Savings Estimate  │
                            │ Recommendations   │
                            │ Resource Details  │
                            └───────────────────┘