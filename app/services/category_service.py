from typing import List, Optional
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import AsphaltCategory, AsphaltSubCategory, AsphaltType


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_categories(self) -> List[AsphaltCategory]:
        """Get all categories with their subcategories."""
        result = await self.session.execute(
            select(AsphaltCategory)
            .options(selectinload(AsphaltCategory.subcategories))
            .where(AsphaltCategory.is_active == True)
            .order_by(AsphaltCategory.name)
        )
        return list(result.scalars().all())

    async def get_categories_light(self) -> List[AsphaltCategory]:
        """Get all active categories without loading relationships (faster)."""
        result = await self.session.execute(
            select(AsphaltCategory)
            .where(AsphaltCategory.is_active == True)
            .order_by(AsphaltCategory.name)
        )
        return list(result.scalars().all())

    async def get_category_by_id(self, category_id: int) -> Optional[AsphaltCategory]:
        """Get category by ID with subcategories."""
        result = await self.session.execute(
            select(AsphaltCategory)
            .options(selectinload(AsphaltCategory.subcategories))
            .where(AsphaltCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def create_category(self, name: str, description: Optional[str] = None) -> AsphaltCategory:
        """Create a new category."""
        category = AsphaltCategory(name=name, description=description)
        self.session.add(category)
        await self.session.flush()
        return category

    async def get_subcategories_by_category(self, category_id: int) -> List[AsphaltSubCategory]:
        """Get all subcategories for a category (with materials - slower)."""
        result = await self.session.execute(
            select(AsphaltSubCategory)
            .options(selectinload(AsphaltSubCategory.asphalt_types))
            .where(AsphaltSubCategory.category_id == category_id)
            .where(AsphaltSubCategory.is_active == True)
            .order_by(AsphaltSubCategory.name)
        )
        return list(result.scalars().all())

    async def get_subcategories_light(self, category_id: int) -> List[AsphaltSubCategory]:
        """Get all subcategories for a category without loading materials (faster)."""
        result = await self.session.execute(
            select(AsphaltSubCategory)
            .where(AsphaltSubCategory.category_id == category_id)
            .where(AsphaltSubCategory.is_active == True)
            .order_by(AsphaltSubCategory.name)
        )
        return list(result.scalars().all())

    async def get_subcategory_by_id(self, subcategory_id: int) -> Optional[AsphaltSubCategory]:
        """Get subcategory by ID with materials."""
        result = await self.session.execute(
            select(AsphaltSubCategory)
            .options(selectinload(AsphaltSubCategory.asphalt_types))
            .where(AsphaltSubCategory.id == subcategory_id)
        )
        return result.scalar_one_or_none()

    async def create_subcategory(
        self, 
        category_id: int, 
        name: str, 
        description: Optional[str] = None
    ) -> AsphaltSubCategory:
        """Create a new subcategory."""
        subcategory = AsphaltSubCategory(
            category_id=category_id,
            name=name,
            description=description
        )
        self.session.add(subcategory)
        await self.session.flush()
        return subcategory

    async def get_materials_by_subcategory(self, subcategory_id: int) -> List[AsphaltType]:
        """Get all materials for a subcategory."""
        result = await self.session.execute(
            select(AsphaltType)
            .where(AsphaltType.subcategory_id == subcategory_id)
            .where(AsphaltType.is_active == True)
            .order_by(AsphaltType.name)
        )
        return list(result.scalars().all())

    async def get_material_by_id(self, material_id: int) -> Optional[AsphaltType]:
        """Get a single material/asphalt type by ID."""
        result = await self.session.execute(
            select(AsphaltType).where(AsphaltType.id == material_id)
        )
        return result.scalar_one_or_none()

    async def create_material(
        self,
        subcategory_id: int,
        name: str,
        cost_price_per_m2: Decimal,
        price_per_m2: Decimal
    ) -> AsphaltType:
        """Create a new material."""
        material = AsphaltType(
            subcategory_id=subcategory_id,
            name=name,
            cost_price_per_m2=cost_price_per_m2,
            price_per_m2=price_per_m2
        )
        self.session.add(material)
        await self.session.flush()
        return material

    async def delete_category(self, category_id: int) -> None:
        await self.session.execute(delete(AsphaltCategory).where(AsphaltCategory.id == category_id))
        await self.session.flush()

    async def delete_subcategory(self, subcategory_id: int) -> None:
        await self.session.execute(delete(AsphaltSubCategory).where(AsphaltSubCategory.id == subcategory_id))
        await self.session.flush()

    async def delete_material(self, material_id: int) -> None:
        await self.session.execute(delete(AsphaltType).where(AsphaltType.id == material_id))
        await self.session.flush()
