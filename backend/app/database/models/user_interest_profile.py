import uuid

from sqlalchemy import Integer, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class UserInterestProfile(Base, TimestampMixin):
    __tablename__ = "user_interest_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    domain_weights: Mapped[dict] = mapped_column(JSONB, nullable=False)
    context_prose: Mapped[str | None] = mapped_column(Text)
    channel_notes: Mapped[dict | None] = mapped_column(JSONB)
