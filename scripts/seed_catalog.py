"""
Seed script for generating the initial electronics catalog.
"""

import asyncio
import os
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.category import Category
from app.models.product import Product
from app.models.product_relationship import ProductRelationship
from app.models.product_variant import ProductVariant
from app.models.inventory import Inventory
from app.models.tenant import Tenant
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.product_relationship import ProductRelationshipRepository
from app.services.category import CategoryService
from app.services.product import ProductService
from app.services.inventory import InventoryService
from app.services.product_relationship import ProductRelationshipService
from app.schemas.category import CategoryCreate
from app.schemas.product import ProductCreate
from app.schemas.inventory import InventoryUpdate
from app.schemas.product_relationship import RelationshipCreate
from app.schemas.product_variant import VariantCreate


# Use a separate test tenant for seeding if none exists
TEST_TENANT_NAME = "TechWorld"
TEST_TENANT_SLUG = "techworld"


async def main():
    database_url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://razorgrowth:razorgrowth_dev@localhost:5432/razorgrowth")
    engine = create_async_engine(database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as db:
        print("Starting seed...")

        # 1. Get or create Tenant
        from sqlalchemy import select
        tenant = (await db.execute(select(Tenant).where(Tenant.slug == TEST_TENANT_SLUG))).scalar_one_or_none()
        if not tenant:
            tenant = Tenant(
                name=TEST_TENANT_NAME,
                slug=TEST_TENANT_SLUG,
                default_currency="INR",
            )
            db.add(tenant)
            await db.commit()
            await db.refresh(tenant)
            print(f"Created Tenant: {tenant.name} ({tenant.id})")
        else:
            print(f"Using existing Tenant: {tenant.name} ({tenant.id})")

        tenant_id = tenant.id

        # 2. Categories
        cat_electronics = await CategoryService.create(db, tenant_id, CategoryCreate(
            name="Electronics",
            slug="electronics",
            description="All electronic items",
        ))
        
        cat_laptops = await CategoryService.create(db, tenant_id, CategoryCreate(
            name="Laptops",
            slug="laptops",
            description="Laptops and Notebooks",
            parent_id=cat_electronics.id
        ))
        
        cat_smartphones = await CategoryService.create(db, tenant_id, CategoryCreate(
            name="Smartphones",
            slug="smartphones",
            description="Mobile Phones",
            parent_id=cat_electronics.id
        ))

        cat_accessories = await CategoryService.create(db, tenant_id, CategoryCreate(
            name="Accessories",
            slug="accessories",
            description="Tech Accessories",
            parent_id=cat_electronics.id
        ))

        cat_audio = await CategoryService.create(db, tenant_id, CategoryCreate(
            name="Audio",
            slug="audio",
            description="Headphones and Speakers",
            parent_id=cat_electronics.id
        ))

        print("Created Categories.")

        # 3. Products
        laptop_1 = await ProductService.create(db, tenant_id, ProductCreate(
            sku="LAP-PRO-16",
            name="MacBook Pro 16-inch",
            slug="macbook-pro-16",
            category_id=cat_laptops.id,
            brand="Apple",
            base_price=Decimal("249900.00"),
            description="M3 Max chip, 36GB RAM, 1TB SSD",
            metadata={"ram": "36GB", "storage": "1TB", "processor": "M3 Max"}
        ))

        laptop_2 = await ProductService.create(db, tenant_id, ProductCreate(
            sku="LAP-XPS-15",
            name="Dell XPS 15",
            slug="dell-xps-15",
            category_id=cat_laptops.id,
            brand="Dell",
            base_price=Decimal("189900.00"),
            description="Intel Core i9, 32GB RAM, 1TB SSD, RTX 4070",
            metadata={"ram": "32GB", "storage": "1TB", "processor": "Intel i9", "gpu": "RTX 4070"}
        ))

        phone_1 = await ProductService.create(db, tenant_id, ProductCreate(
            sku="PHN-IP15-PRO",
            name="iPhone 15 Pro",
            slug="iphone-15-pro",
            category_id=cat_smartphones.id,
            brand="Apple",
            base_price=Decimal("134900.00"),
            description="A17 Pro chip, Titanium design, 256GB",
            metadata={"storage": "256GB", "camera": "48MP", "processor": "A17 Pro"}
        ))

        phone_2 = await ProductService.create(db, tenant_id, ProductCreate(
            sku="PHN-S24-ULTRA",
            name="Samsung Galaxy S24 Ultra",
            slug="samsung-galaxy-s24-ultra",
            category_id=cat_smartphones.id,
            brand="Samsung",
            base_price=Decimal("129999.00"),
            description="Snapdragon 8 Gen 3, AI features, 512GB",
            metadata={"storage": "512GB", "camera": "200MP", "processor": "Snapdragon 8 Gen 3"}
        ))

        audio_1 = await ProductService.create(db, tenant_id, ProductCreate(
            sku="AUD-APP-2",
            name="AirPods Pro (2nd Gen)",
            slug="airpods-pro-2",
            category_id=cat_audio.id,
            brand="Apple",
            base_price=Decimal("24900.00"),
            description="Active Noise Cancellation, USB-C",
            metadata={"type": "Earbuds", "anc": True}
        ))

        audio_2 = await ProductService.create(db, tenant_id, ProductCreate(
            sku="AUD-SONY-XM5",
            name="Sony WH-1000XM5",
            slug="sony-wh-1000xm5",
            category_id=cat_audio.id,
            brand="Sony",
            base_price=Decimal("29990.00"),
            description="Over-ear Noise Cancelling Headphones",
            metadata={"type": "Over-ear", "anc": True}
        ))

        acc_1 = await ProductService.create(db, tenant_id, ProductCreate(
            sku="ACC-USB-C-30W",
            name="30W USB-C Power Adapter",
            slug="30w-usb-c-power-adapter",
            category_id=cat_accessories.id,
            brand="Generic",
            base_price=Decimal("1900.00"),
            description="Fast charger for smartphones and tablets",
            metadata={"wattage": "30W", "port": "USB-C"}
        ))

        print("Created Products.")

        # 4. Inventory
        await InventoryService.update(db, tenant_id, laptop_1.id, InventoryUpdate(available_quantity=5))
        await InventoryService.update(db, tenant_id, laptop_2.id, InventoryUpdate(available_quantity=12))
        await InventoryService.update(db, tenant_id, phone_1.id, InventoryUpdate(available_quantity=20))
        await InventoryService.update(db, tenant_id, phone_2.id, InventoryUpdate(available_quantity=15))
        await InventoryService.update(db, tenant_id, audio_1.id, InventoryUpdate(available_quantity=50))
        await InventoryService.update(db, tenant_id, audio_2.id, InventoryUpdate(available_quantity=30))
        await InventoryService.update(db, tenant_id, acc_1.id, InventoryUpdate(available_quantity=100))

        print("Updated Inventory.")

        # 5. Product Relationships (Cross-Sells, Accessories)
        # iPhone -> AirPods Pro
        await ProductRelationshipService.create(db, tenant_id, phone_1.id, RelationshipCreate(
            target_product_id=audio_1.id,
            relationship_type="ACCESSORY",
            score=Decimal("0.95"),
        ))

        # iPhone -> 30W Charger
        await ProductRelationshipService.create(db, tenant_id, phone_1.id, RelationshipCreate(
            target_product_id=acc_1.id,
            relationship_type="ACCESSORY",
            score=Decimal("0.85"),
        ))

        # MacBook -> AirPods Pro
        await ProductRelationshipService.create(db, tenant_id, laptop_1.id, RelationshipCreate(
            target_product_id=audio_1.id,
            relationship_type="CROSS_SELL",
            score=Decimal("0.80"),
        ))

        # Galaxy S24 -> Sony XM5
        await ProductRelationshipService.create(db, tenant_id, phone_2.id, RelationshipCreate(
            target_product_id=audio_2.id,
            relationship_type="CROSS_SELL",
            score=Decimal("0.75"),
        ))

        print("Created Product Relationships.")
        print("Seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
