"""
ProductRelationship model.

Maps directional relationships between products within a tenant.
Types: ACCESSORY, COMPATIBLE, CROSS_SELL, UPSELL, ALTERNATIVE, BUNDLE_ITEM, REPLACEMENT.
Score indicates relationship strength (0.0 to 1.0).
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


RELATIONSHIP_TYPES = (
    "ACCESSORY",
    "COMPATIBLE",
    "CROSS_SELL",
    "UPSELL",
    "ALTERNATIVE",
    "BUNDLE_ITEM",
    "REPLACEMENT",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProductRelationship(Base):
    __tablename__ = "product_relationships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )

    relationship_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False,
        default=Decimal("0.0"),
    )

    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="'{}'",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "source_product_id", "target_product_id", "relationship_type",
            name="uq_product_relationship",
        ),
    )

    # Relationships
    source_product: Mapped["Product"] = relationship(
        "Product",
        foreign_keys=[source_product_id],
        lazy="selectin",
    )

    target_product: Mapped["Product"] = relationship(
        "Product",
        foreign_keys=[target_product_id],
        lazy="selectin",
    )
