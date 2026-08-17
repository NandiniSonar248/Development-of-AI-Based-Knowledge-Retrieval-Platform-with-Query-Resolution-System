"""Query record persistence and analytics aggregation."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query import QueryRecord


def _normalize(question: str) -> str:
    """Normalize a question for frequency grouping (lowercased + collapsed whitespace)."""
    return " ".join(question.strip().lower().split())[:500]


class QueryRepository:
    """Data-access layer for query records and analytics."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        question: str,
        answer: str,
        confidence: float,
    ) -> QueryRecord:
        """Persist a single answered query."""
        record = QueryRecord(
            user_id=user_id,
            question=question.strip(),
            question_normalized=_normalize(question),
            answer=answer,
            confidence=confidence,
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def count(self, user_id: UUID) -> int:
        """Total number of queries for a user."""
        stmt = select(func.count(QueryRecord.id)).where(QueryRecord.user_id == user_id)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def recent(self, user_id: UUID, limit: int = 50) -> list[QueryRecord]:
        """Most recent queries for a user, newest first."""
        stmt = (
            select(QueryRecord)
            .where(QueryRecord.user_id == user_id)
            .order_by(desc(QueryRecord.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def top_questions(self, user_id: UUID, limit: int = 10) -> list[tuple[str, int]]:
        """Most frequently asked questions (by normalized text) for a user."""
        stmt = (
            select(QueryRecord.question_normalized, func.count(QueryRecord.id).label("n"))
            .where(QueryRecord.user_id == user_id)
            .group_by(QueryRecord.question_normalized)
            .order_by(desc("n"))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def confidence_distribution(self, user_id: UUID) -> dict[str, int]:
        """Bucket the user's queries by confidence into named bins."""
        bins = {"high": 0, "moderate": 0, "low": 0, "very_low": 0}
        stmt = select(QueryRecord.confidence).where(QueryRecord.user_id == user_id)
        result = await self._session.execute(stmt)
        for (score,) in result.all():
            if score >= 0.7:
                bins["high"] += 1
            elif score >= 0.5:
                bins["moderate"] += 1
            elif score >= 0.3:
                bins["low"] += 1
            else:
                bins["very_low"] += 1
        return bins

    async def knowledge_gaps(
        self,
        user_id: UUID,
        threshold: float,
        limit: int = 50,
    ) -> list[QueryRecord]:
        """Queries whose confidence fell below the gap threshold."""
        stmt = (
            select(QueryRecord)
            .where(QueryRecord.user_id == user_id, QueryRecord.confidence < threshold)
            .order_by(desc(QueryRecord.created_at))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())