"""Shared platform types."""

from enum import StrEnum


class AgentType(StrEnum):
    KUBERNETES = "kubernetes"
    AWS = "aws"
