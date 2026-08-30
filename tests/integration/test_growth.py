import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tenant import Tenant
from app.models.product import Product
from app.models.category import Category
from app.models.growth import Recommendation, Experiment, ExperimentParticipant, AnalyticsEvent

@pytest.fixture
async def growth_tenant_headers(tenant: Tenant):
    return {
        "X-Tenant-ID": str(tenant.id)
    }

@pytest.fixture
async def sample_product(db: AsyncSession, tenant: Tenant):
    cat = Category(tenant_id=tenant.id, name="Growth", slug="growth")
    db.add(cat)
    await db.flush()
    prod = Product(tenant_id=tenant.id, category_id=cat.id, sku="TEST-SKU-1", name="Test Product", slug="test-product", description="Test", base_price=10.0)
    db.add(prod)
    await db.commit()
    return prod


@pytest.mark.asyncio
async def test_get_recommendations(client: AsyncClient, growth_tenant_headers, db: AsyncSession, tenant: Tenant, sample_product: Product):
    rec = Recommendation(
        tenant_id=tenant.id,
        product_id=sample_product.id,
        score=0.95,
        reason="Popular"
    )
    db.add(rec)
    await db.commit()
    
    res = await client.get("/api/v1/recommendations", headers=growth_tenant_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["product_id"] == str(sample_product.id)
    assert data[0]["score"] == 0.95

@pytest.mark.asyncio
async def test_participate_experiment(client: AsyncClient, growth_tenant_headers, db: AsyncSession, tenant: Tenant):
    exp = Experiment(
        tenant_id=tenant.id,
        name="pricing_test_1",
        description="Test pricing",
        variants={"control": 50, "treatment": 50}
    )
    db.add(exp)
    await db.commit()
    
    headers = growth_tenant_headers.copy()
    headers["X-Session-ID"] = "session_123"
    
    res = await client.post(
        "/api/v1/experiments/participate",
        headers=headers,
        json={"experiment_name": "pricing_test_1"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["experiment_id"] == str(exp.id)
    assert data["variant"] in ["control", "treatment"]
    
    # Check idempotent participation
    res2 = await client.post(
        "/api/v1/experiments/participate",
        headers=headers,
        json={"experiment_name": "pricing_test_1"}
    )
    assert res2.status_code == 200
    assert res2.json()["variant"] == data["variant"]

@pytest.mark.asyncio
async def test_track_event(client: AsyncClient, growth_tenant_headers):
    res = await client.post(
        "/api/v1/analytics/events",
        headers=growth_tenant_headers,
        json={
            "event_type": "page_view",
            "payload": {"url": "/home", "referrer": "google"}
        }
    )
    assert res.status_code == 201
    data = res.json()
    assert data["event_type"] == "page_view"
    assert "id" in data
