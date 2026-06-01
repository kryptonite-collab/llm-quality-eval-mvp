"""Message rating repository for database operations."""

"""Message rating repository (SQLite sync)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session, selectinload

from app.db.models.message_rating import MessageRating


def get_rating_by_message_and_user(
    db: Session,
    message_id: str,
    user_id: str,
) -> MessageRating | None:
    """Get a user's rating for a specific message."""
    query = select(MessageRating).where(
        MessageRating.message_id == message_id,
        MessageRating.user_id == user_id,
    )
    result = db.execute(query)
    return result.scalar_one_or_none()


def create_rating(
    db: Session,
    *,
    message_id: str,
    user_id: str,
    rating: int,
    comment: str | None = None,
) -> MessageRating:
    """Create a new rating.

    Note: The unique constraint on (message_id, user_id) prevents duplicates
    at the database level. Callers should handle IntegrityError.
    """
    rating_obj = MessageRating(
        message_id=message_id,
        user_id=user_id,
        rating=rating,
        comment=comment,
    )
    db.add(rating_obj)
    db.flush()
    db.refresh(rating_obj)
    return rating_obj


def update_rating(
    db: Session,
    rating: MessageRating,
    *,
    new_rating: int,
    comment: str | None = None,
) -> MessageRating:
    """Update an existing rating."""
    rating.rating = new_rating
    rating.comment = comment
    db.flush()
    db.refresh(rating)
    return rating


def delete_rating(db: Session, rating: MessageRating) -> None:
    """Delete a rating."""
    db.delete(rating)
    db.flush()


def get_ratings_for_message(
    db: Session,
    message_id: str,
) -> list[MessageRating]:
    """Get all ratings for a message."""
    query = select(MessageRating).where(MessageRating.message_id == message_id)
    result = db.execute(query)
    return list(result.scalars().all())


def get_user_ratings_for_messages(
    db: Session,
    *,
    message_ids: list[str],
    user_id: str,
) -> dict[str, int]:
    """Return mapping of message_id → rating value for a single user."""
    if not message_ids:
        return {}
    query = select(MessageRating).where(
        MessageRating.message_id.in_(message_ids),
        MessageRating.user_id == user_id,
    )
    result = db.execute(query)
    return {rating.message_id: rating.rating for rating in result.scalars().all()}


def get_rating_counts_for_messages(
    db: Session,
    *,
    message_ids: list[str],
) -> dict[str, dict[str, int]]:
    """Return mapping of message_id → {likes, dislikes} counts."""
    if not message_ids:
        return {}
    query = (
        select(
            MessageRating.message_id,
            func.sum(case((MessageRating.rating == 1, 1), else_=0)).label("likes"),
            func.sum(case((MessageRating.rating == -1, 1), else_=0)).label("dislikes"),
        )
        .where(MessageRating.message_id.in_(message_ids))
        .group_by(MessageRating.message_id)
    )
    result = db.execute(query)
    return {
        row.message_id: {"likes": row.likes or 0, "dislikes": row.dislikes or 0}
        for row in result.all()
    }


def get_ratings_with_users_for_messages(
    db: Session,
    *,
    message_ids: list[str],
) -> list[tuple[MessageRating, Any]]:
    """Return ratings joined with users for the given message IDs (admin export)."""
    if not message_ids:
        return []
    from app.db.models.user import User

    query = (
        select(MessageRating, User)
        .join(User, MessageRating.user_id == User.id)
        .where(MessageRating.message_id.in_(message_ids))
    )
    result = db.execute(query)
    return [(rating, user) for rating, user in result.all()]


def list_ratings(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    rating_filter: int | None = None,
    with_comments_only: bool = False,
) -> tuple[list[MessageRating], int]:
    """List ratings with optional filters."""
    query = select(MessageRating)

    if rating_filter is not None:
        query = query.where(MessageRating.rating == rating_filter)

    if with_comments_only:
        query = query.where(MessageRating.comment.isnot(None), MessageRating.comment != "")

    # Count query
    count_query = select(func.count()).select_from(query.subquery())
    count_result = db.execute(count_query)
    total = count_result.scalar_one()

    # Apply ordering and pagination
    query = query.order_by(MessageRating.created_at.desc()).offset(skip).limit(limit)

    # Eager load relationships
    query = query.options(
        selectinload(MessageRating.message),
        selectinload(MessageRating.user),
    )

    result = db.execute(query)
    items = list(result.scalars().all())

    return items, total


def get_rating_summary(
    db: Session,
    *,
    days: int = 30,
) -> dict[str, Any]:
    """Get aggregated rating statistics."""
    cutoff_date = datetime.now(UTC) - timedelta(days=days)

    # Total counts
    counts_query = select(
        func.count().label("total"),
        func.sum(case((MessageRating.rating == 1, 1), else_=0)).label("likes"),
        func.sum(case((MessageRating.rating == -1, 1), else_=0)).label("dislikes"),
        func.avg(MessageRating.rating).label("avg_rating"),
        func.sum(
            case((and_(MessageRating.comment.isnot(None), MessageRating.comment != ""), 1), else_=0)
        ).label("with_comments"),
    ).where(MessageRating.created_at >= cutoff_date)

    result = db.execute(counts_query)
    row = result.one()

    # Daily breakdown
    daily_query = (
        select(
            func.date(MessageRating.created_at).label("date"),
            func.sum(case((MessageRating.rating == 1, 1), else_=0)).label("likes"),
            func.sum(case((MessageRating.rating == -1, 1), else_=0)).label("dislikes"),
        )
        .where(MessageRating.created_at >= cutoff_date)
        .group_by(func.date(MessageRating.created_at))
        .order_by(func.date(MessageRating.created_at))
    )

    daily_result = db.execute(daily_query)
    ratings_by_day = [
        {"date": str(row.date), "likes": row.likes or 0, "dislikes": row.dislikes or 0}
        for row in daily_result
    ]

    return {
        "total_ratings": row.total or 0,
        "like_count": row.likes or 0,
        "dislike_count": row.dislikes or 0,
        "average_rating": float(row.avg_rating) if row.avg_rating else 0.0,
        "with_comments": row.with_comments or 0,
        "ratings_by_day": ratings_by_day,
    }
