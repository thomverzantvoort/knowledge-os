from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.database.models.enums import ContentKind, ProcessingStatus, UserStatus


class EnrichmentOut(BaseModel):
    blurb: str
    tags: list[str]
    content_type: str
    domain_matches: list[str]
    relevance_score: float
    input_kind: str
    enriched_at: str


class ContentItemOut(BaseModel):
    id: UUID
    subscription_id: UUID
    title: str
    description: str | None
    url: str
    thumbnail_url: str | None
    author: str | None
    published_at: datetime
    kind: ContentKind
    user_status: UserStatus
    processing_status: ProcessingStatus
    enrichment: EnrichmentOut | None


class ArtifactOut(BaseModel):
    chapters: list[dict]
    summary: dict
    model: str | None
    generated_at: datetime


class ContentItemDetailOut(ContentItemOut):
    artifact: ArtifactOut | None


class SubscriptionOut(BaseModel):
    id: UUID
    title: str | None
    url: str | None


class PaginatedItemsOut(BaseModel):
    items: list[ContentItemOut]
    total: int
    limit: int
    offset: int


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StatusUpdateIn(BaseModel):
    status: UserStatus = Field(description="New triage status for the content item")
