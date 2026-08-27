"""
Product model.

Core commerce entity. Each product belongs to a tenant and a category.
Uses JSONB metadata for flexible, category-specific attributes
(e.g., RAM, storage for laptops; camera, battery for phones).
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

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

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    sku: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVE",
    )

    brand: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    base_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
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

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "sku", name="uq_product_tenant_sku"),
        UniqueConstraint("tenant_id", "slug", name="uq_product_tenant_slug"),
    )

    # Relationships
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="products",
        lazy="selectin",
    )

    variants: Mapped[list["ProductVariant"]] = relationship(
        "ProductVariant",
        back_populates="product",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    inventory: Mapped[list["Inventory"]] = relationship(
        "Inventory",
        back_populates="product",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
