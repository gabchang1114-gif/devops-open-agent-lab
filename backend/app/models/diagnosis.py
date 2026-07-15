from pydantic import BaseModel, Field, model_validator


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "devops-open-agent"
    version: str = "0.1.0"


class SystemInfoResponse(BaseModel):
    service: str = "devops-open-agent"
    environment: str
    llm_provider: str
    multi_cluster_enabled: bool
    topology_graph_enabled: bool
    memory_enabled: bool


class InvestigationRequest(BaseModel):
    """Investigation request supporting Kubernetes and AWS troubleshooting agents."""

    cluster_id: str | None = Field(
        default=None,
        description="Target cluster identifier for Kubernetes investigations",
        examples=["prod-us-east-1"],
    )
    namespace: str | None = None
    resource_type: str | None = None
    resource_name: str | None = None
    query: str | None = None
    include_ai: bool = False
    include_rag: bool = Field(
        default=False,
        description="Augment AI analysis with similar past investigations from Qdrant (RAG)",
    )
    include_judge: bool = Field(
        default=False,
        description="Run a secondary AI to verify the primary diagnosis (LLM-as-a-Judge)",
    )
    judge_provider: str | None = Field(
        default=None,
        description="LLM provider for the judge (overrides JUDGE_LLM_PROVIDER env var)",
    )
    judge_model: str | None = Field(
        default=None,
        description="Model name for the judge (overrides JUDGE_*_MODEL env var)",
    )
    agent_type: str = Field(
        default="kubernetes",
        description="Troubleshooting agent type, e.g. kubernetes or aws",
    )
    account_id: str | None = Field(
        default=None,
        description="AWS account ID for AWS investigations",
    )
    region: str | None = Field(
        default=None,
        description="AWS region for AWS investigations",
    )
    cloudwatch_window: str = Field(
        default="24h",
        description="CloudWatch lookback window for AWS investigations",
    )
    issue_type: str = Field(
        default="full_scan",
        description="AWS troubleshooting mode",
    )

    @model_validator(mode="after")
    def validate_scope(self) -> "InvestigationRequest":
        if self.agent_type == "aws":
            if not self.account_id or not self.region:
                raise ValueError("account_id and region are required for AWS investigations")
        elif self.agent_type == "cloud_cost":
            if not self.account_id or not self.region:
                raise ValueError("account_id and region are required for Cloud Cost investigations")
        elif not self.cluster_id:
            raise ValueError("cluster_id is required for Kubernetes investigations")
        return self


class DiagnoseRequest(BaseModel):
    """Diagnose an existing investigation payload without running kubectl again."""

    investigation_payload: dict = Field(
        ...,
        description="Investigation payload returned by POST /api/v1/investigate",
    )


class DiagnosisEvidence(BaseModel):
    source: str
    detail: str


class PodIssueDiagnosis(BaseModel):
    """Independent diagnosis for a single problematic pod."""

    pod: str
    namespace: str
    status: str
    reason: str
    root_cause: str
    summary: str
    evidence: list[DiagnosisEvidence] = Field(default_factory=list)
    suggested_fix: str
    kubectl_commands: list[str] = Field(default_factory=list)
    validation_steps: list[str] = Field(default_factory=list)
    confidence_score: int = Field(ge=0, le=100, default=0)


class JudgeVerdict(BaseModel):
    """LLM-as-a-Judge evaluation of a primary diagnosis."""

    verdict: str = Field(description="agree, partially_agree, or disagree")
    confidence_score: int = Field(ge=0, le=100)
    reasoning: str
    factual_issues: list[str] = Field(default_factory=list)
    missed_evidence: list[str] = Field(default_factory=list)
    command_safety_concerns: list[str] = Field(default_factory=list)
    suggested_improvements: list[str] = Field(default_factory=list)
    llm_provider: str | None = None
    llm_error: str | None = None


class DiagnosisResult(BaseModel):
    """Structured AI root cause analysis."""

    root_cause: str
    summary: str
    evidence: list[DiagnosisEvidence] = Field(default_factory=list)
    suggested_fix: str
    kubectl_commands: list[str] = Field(default_factory=list)
    validation_steps: list[str] = Field(default_factory=list)
    prevention_recommendation: str = ""
    confidence_score: int = Field(ge=0, le=100)
    confidence_reason: str
    needs_more_data: bool = False
    additional_data_needed: list[str] = Field(default_factory=list)
    issue_diagnoses: list[PodIssueDiagnosis] = Field(default_factory=list)
    llm_provider: str | None = None
    llm_error: str | None = None
    judge_verdict: JudgeVerdict | None = None


class DiagnoseResponse(BaseModel):
    status: str
    diagnosis: DiagnosisResult
    error: str | None = None
