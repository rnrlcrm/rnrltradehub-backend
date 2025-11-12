"""
CRUD helper functions for RNRL TradeHub backend.

This module provides reusable functions for common CRUD operations
to eliminate code duplication across route handlers.
"""
from typing import TypeVar, Type, Optional, List, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta

# Type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


def get_entity_by_id(
    db: Session,
    model: Type[ModelType],
    entity_id: Any,
    entity_name: str,
    id_field: str = "id"
) -> ModelType:
    """
    Get an entity by ID or raise 404 error.
    
    Args:
        db: Database session.
        model: SQLAlchemy model class.
        entity_id: ID value to search for.
        entity_name: Human-readable entity name for error messages.
        id_field: Name of the ID field (default: "id").
        
    Returns:
        Entity instance if found.
        
    Raises:
        HTTPException: 404 error if entity not found.
    """
    entity = db.query(model).filter(
        getattr(model, id_field) == entity_id
    ).first()
    
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} not found"
        )
    
    return entity


def get_entity_by_field(
    db: Session,
    model: Type[ModelType],
    field_name: str,
    field_value: Any,
    entity_name: str
) -> Optional[ModelType]:
    """
    Get an entity by a specific field value.
    
    Args:
        db: Database session.
        model: SQLAlchemy model class.
        field_name: Name of the field to filter by.
        field_value: Value to search for.
        entity_name: Human-readable entity name for error messages.
        
    Returns:
        Entity instance if found, None otherwise.
    """
    return db.query(model).filter(
        getattr(model, field_name) == field_value
    ).first()


def list_entities(
    db: Session,
    model: Type[ModelType],
    skip: int = 0,
    limit: int = 100
) -> List[ModelType]:
    """
    List entities with pagination.
    
    Args:
        db: Database session.
        model: SQLAlchemy model class.
        skip: Number of records to skip (offset).
        limit: Maximum number of records to return.
        
    Returns:
        List of entity instances.
    """
    return db.query(model).offset(skip).limit(limit).all()


def check_entity_exists(
    db: Session,
    model: Type[ModelType],
    field_name: str,
    field_value: Any,
    entity_name: str,
    exclude_id: Optional[Any] = None,
    id_field: str = "id"
) -> None:
    """
    Check if an entity with a specific field value already exists.
    
    Raises HTTPException if entity exists.
    
    Args:
        db: Database session.
        model: SQLAlchemy model class.
        field_name: Name of the field to check.
        field_value: Value to check for.
        entity_name: Human-readable entity name for error messages.
        exclude_id: Optional ID to exclude from check (for updates).
        id_field: Name of the ID field (default: "id").
        
    Raises:
        HTTPException: 400 error if entity already exists.
    """
    query = db.query(model).filter(
        getattr(model, field_name) == field_value
    )
    
    # Exclude specific ID if provided (for update operations)
    if exclude_id is not None:
        query = query.filter(
            getattr(model, id_field) != exclude_id
        )
    
    existing = query.first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{entity_name} with {field_name} '{field_value}' already exists"
        )


def soft_delete_entity(
    db: Session,
    entity: ModelType,
    active_field: str = "is_active"
) -> None:
    """
    Soft delete an entity by setting its active flag to False.
    
    Args:
        db: Database session.
        entity: Entity instance to soft delete.
        active_field: Name of the active status field (default: "is_active").
    """
    setattr(entity, active_field, False)
    db.commit()


def hard_delete_entity(
    db: Session,
    entity: ModelType
) -> None:
    """
    Hard delete an entity from the database.
    
    Args:
        db: Database session.
        entity: Entity instance to delete.
    """
    db.delete(entity)
    db.commit()
