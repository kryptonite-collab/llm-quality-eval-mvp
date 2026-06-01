"""ConversationShare repository (SQLite sync)."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.db.models.conversation import Conversation
from app.db.models.conversation_share import ConversationShare


def get_by_id(db: DBSession, share_id: str) -> ConversationShare | None:
    """Get a share by ID."""
    return db.get(ConversationShare, share_id)


def get_share(db: DBSession, conversation_id: str, shared_with: str) -> ConversationShare | None:
    """Get a share by conversation + user composite key."""
    result = db.execute(
        select(ConversationShare).where(
            ConversationShare.conversation_id == conversation_id,
            ConversationShare.shared_with == shared_with,
        )
    )
    return result.scalar_one_or_none()


def get_by_token(db: DBSession, token: str) -> ConversationShare | None:
    """Get a share by its public token."""
    result = db.execute(select(ConversationShare).where(ConversationShare.share_token == token))
    return result.scalar_one_or_none()


def get_shares_for_conversation(db: DBSession, conversation_id: str) -> list[ConversationShare]:
    """List all shares for a conversation."""
    result = db.execute(
        select(ConversationShare)
        .where(ConversationShare.conversation_id == conversation_id)
        .order_by(ConversationShare.created_at.desc())
    )
    return list(result.scalars().all())


def get_conversations_shared_with_user(
    db: DBSession, user_id: str, *, skip: int = 0, limit: int = 50
) -> list[Conversation]:
    """Get conversations shared with a specific user."""
    result = db.execute(
        select(Conversation)
        .join(ConversationShare, ConversationShare.conversation_id == Conversation.id)
        .where(ConversationShare.shared_with == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


def count_conversations_shared_with_user(db: DBSession, user_id: str) -> int:
    """Count conversations shared with a specific user."""
    result = db.scalar(
        select(func.count())
        .select_from(ConversationShare)
        .where(ConversationShare.shared_with == user_id)
    )
    return result or 0


def user_has_access(db: DBSession, conversation_id: str, user_id: str) -> ConversationShare | None:
    """Check if user has any share access to a conversation."""
    return get_share(db, conversation_id, user_id)


def create(
    db: DBSession,
    *,
    conversation_id: str,
    shared_by: str,
    shared_with: str | None = None,
    share_token: str | None = None,
    permission: str = "view",
) -> ConversationShare:
    """Create a new conversation share."""
    share = ConversationShare(
        conversation_id=conversation_id,
        shared_by=shared_by,
        shared_with=shared_with,
        share_token=share_token,
        permission=permission,
    )
    db.add(share)
    db.flush()
    db.refresh(share)
    return share


def update(
    db: DBSession,
    *,
    db_share: ConversationShare,
    update_data: dict,
) -> ConversationShare:
    """Update a conversation share."""
    for field, value in update_data.items():
        setattr(db_share, field, value)
    db.add(db_share)
    db.flush()
    db.refresh(db_share)
    return db_share


def delete(db: DBSession, share_id: str) -> bool:
    """Delete a share by ID."""
    share = get_by_id(db, share_id)
    if not share:
        return False
    db.delete(share)
    db.flush()
    return True
