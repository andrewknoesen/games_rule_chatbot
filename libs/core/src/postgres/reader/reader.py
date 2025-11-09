from typing import Any, Generic, Optional, Sequence, Tuple, Type, TypeVar

from sqlalchemy import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import SQLModel, func, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

# Generic type variable for SQLModel models
ModelType = TypeVar("ModelType", bound=SQLModel)


class PostgresReader(Generic[ModelType]):
    """Async PostgreSQL reader for SQLModel models with full type safety."""

    def __init__(self, session: AsyncSession, model_class: Type[ModelType]) -> None:
        """
        Initialize reader with an async session and model class.

        Args:
            session: SQLAlchemy async session
            model_class: The SQLModel class to query
        """
        self.session: AsyncSession = session
        self.model_class: Type[ModelType] = model_class

    async def get_by_id(self, record_id: int) -> Optional[ModelType]:
        """
        Fetch a single record by ID.

        Args:
            record_id: Primary key of the record

        Returns:
            Model instance or None if not found
        """
        return await self.session.get(self.model_class, record_id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelType]:
        """
        Fetch all records with pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            Sequence of model instances
        """
        statement = select(self.model_class).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_filter(self, **filters: dict[str, Any]) -> Sequence[ModelType]:
        """
        Fetch records matching filter conditions.

        Args:
            **filters: Keyword arguments for filtering (field=value)

        Returns:
            Sequence of matching model instances
        """
        statement: SelectOfScalar[ModelType] = select(self.model_class)

        for field, value in filters.items():
            if hasattr(self.model_class, field):
                statement = statement.where(getattr(self.model_class, field) == value)

        result: Result[Tuple[ModelType]] = await self.session.execute(statement)
        return result.scalars().all()

    async def search_by_text(
        self, field_name: str, search_term: str
    ) -> Sequence[ModelType]:
        """
        Full-text search on a specific field.

        Args:
            field_name: Name of the text field to search
            search_term: Search query string

        Returns:
            Sequence of matching model instances
        """
        statement = select(self.model_class).where(
            getattr(self.model_class, field_name).ilike(f"%{search_term}%")
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_with_relations(
        self, record_id: int, *relations: str
    ) -> Optional[ModelType]:
        """
        Fetch record with eager-loaded relationships.

        Args:
            record_id: Primary key of the record
            relations: Names of relationships to eager load

        Returns:
            Model instance with loaded relationships or None
        """
        statement = select(self.model_class).where(self.model_class.id == record_id)  # type: ignore

        for relation in relations:
            statement = statement.options(
                selectinload(getattr(self.model_class, relation))
            )

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def count(self, **filters: dict[str, Any]) -> int:
        """
        Count records with optional filters.

        Args:
            **filters: Optional keyword arguments for filtering

        Returns:
            Count of matching records
        """
        statement: SelectOfScalar[int] = select(func.count()).select_from(
            self.model_class
        )

        for field, value in filters.items():
            if hasattr(self.model_class, field):
                statement = statement.where(getattr(self.model_class, field) == value)

        result: Result[Tuple[int]] = await self.session.execute(statement)
        return result.scalar() or 0

    async def exists(self, record_id: int) -> bool:
        """
        Check if a record exists.

        Args:
            record_id: Primary key of the record

        Returns:
            True if record exists, False otherwise
        """
        item = await self.session.get(self.model_class, record_id)
        return item is not None

    async def create(self, instance: ModelType) -> ModelType:
        """
        Create a new record.

        Args:
            instance: Model instance to create

        Returns:
            Created model instance with ID
        """
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """
        Update an existing record.

        Args:
            instance: Model instance to update

        Returns:
            Updated model instance
        """
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, record_id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            record_id: Primary key of the record to delete

        Returns:
            True if deleted, False if not found
        """
        instance = await self.session.get(self.model_class, record_id)
        if instance:
            await self.session.delete(instance)
            await self.session.commit()
            return True
        return False
