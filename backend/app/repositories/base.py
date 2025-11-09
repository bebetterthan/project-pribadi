"""
Base Repository - Generic CRUD operations
"""
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with generic CRUD operations"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: str) -> Optional[ModelType]:
        """Get single record by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_dir: str = "desc",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and filtering"""
        query = self.db.query(self.model)
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        # Apply ordering
        if hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_dir == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        query = self.db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()
    
    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create new record"""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, id: str, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """Update existing record"""
        db_obj = self.get(id)
        if not db_obj:
            return None
        
        for key, value in obj_in.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: str) -> bool:
        """Delete record (hard delete)"""
        db_obj = self.get(id)
        if not db_obj:
            return False
        
        self.db.delete(db_obj)
        self.db.commit()
        return True
    
    def soft_delete(self, id: str) -> Optional[ModelType]:
        """Soft delete (set is_active=False) if model supports it"""
        db_obj = self.get(id)
        if not db_obj:
            return None
        
        if hasattr(db_obj, 'is_active'):
            db_obj.is_active = False
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        
        return None

