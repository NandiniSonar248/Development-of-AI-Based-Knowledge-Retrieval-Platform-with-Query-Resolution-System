"""Pydantic schemas for query analytics."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecordQueryRequest(BaseModel):
    """Payload to record a single answered query."""

    question: str = Field(min_length=1, max_length=4000)
    answer: str = Field(max_length=20000)
    confidence: float = Field(ge=0.0, le=1.0)


class QueryRecordPublic(BaseModel):
    """A stored query record returned to the client."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question: str
    answer: str
    confidence: float
    created_at: datetime


class TopQuestion(BaseModel):
    """A frequently asked question with its count."""

    question: str
    count: int


class ConfidenceDistribution(BaseModel):
    """Counts of queries bucketed by confidence."""

    high: int = 0
    moderate: int = 0
    low: int = 0
    very_low: int = 0


class AnalyticsSummary(BaseModel):
    """Per-user analytics summary."""

    total_queries: int
    top_questions: list[TopQuestion]
    confidence_distribution: ConfidenceDistribution
    knowledge_gaps: list[QueryRecordPublic]
    gap_threshold: float