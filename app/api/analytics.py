"""Query analytics & knowledge-gap detection API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.config import get_settings
from app.database.connection import get_db
from app.database.repositories.query_repository import QueryRepository
from app.schemas.analytics import (
    AnalyticsSummary,
    ConfidenceDistribution,
    QueryRecordPublic,
    RecordQueryRequest,
    TopQuestion,
)
from app.schemas.auth import UserPublic

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_query_repository(db: AsyncSession = Depends(get_db)) -> QueryRepository:
    """Provide a query-record repository bound to the request session."""
    return QueryRepository(db)


@router.post("/records", response_model=QueryRecordPublic, status_code=status.HTTP_201_CREATED)
async def record_query(
    body: RecordQueryRequest,
    current_user: UserPublic = Depends(get_current_user),
    repo: QueryRepository = Depends(get_query_repository),
) -> QueryRecordPublic:
    """Record a single answered query for the current user (called by the UI)."""
    try:
        record = await repo.create(
            user_id=current_user.id,
            question=body.question,
            answer=body.answer,
            confidence=body.confidence,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record query: {exc}",
        ) from exc
    return QueryRecordPublic.model_validate(record)


@router.get("/summary", response_model=AnalyticsSummary)
async def analytics_summary(
    current_user: UserPublic = Depends(get_current_user),
    repo: QueryRepository = Depends(get_query_repository),
) -> AnalyticsSummary:
    """Per-user analytics: totals, top questions, confidence bins, and knowledge gaps."""
    gap_threshold = get_settings().retrieval_score_threshold
    total = await repo.count(current_user.id)
    top = await repo.top_questions(current_user.id, limit=10)
    dist = await repo.confidence_distribution(current_user.id)
    gaps = await repo.knowledge_gaps(current_user.id, gap_threshold, limit=50)
    return AnalyticsSummary(
        total_queries=total,
        top_questions=[TopQuestion(question=q, count=n) for q, n in top],
        confidence_distribution=ConfidenceDistribution(**dist),
        knowledge_gaps=[QueryRecordPublic.model_validate(g) for g in gaps],
        gap_threshold=gap_threshold,
    )


@router.get("/recent", response_model=list[QueryRecordPublic])
async def recent_queries(
    current_user: UserPublic = Depends(get_current_user),
    repo: QueryRepository = Depends(get_query_repository),
    limit: int = Query(50, ge=1, le=200),
) -> list[QueryRecordPublic]:
    """Most recent queries for the current user, newest first."""
    records = await repo.recent(current_user.id, limit=limit)
    return [QueryRecordPublic.model_validate(r) for r in records]