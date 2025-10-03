"""
EXPLICACIÓN: Implementación básica SQLAlchemy del repositorio de categorías.
Versión simplificada para funcionalidad básica.
"""

from typing import List, Optional
from sqlalchemy.orm import sessionmaker

from interfaces.repositories.category_repository import CategoryRepository
from domain.entities.category import Category
from infra.database.models import CategoryModel
from infra.database.connection import get_engine

class SQLCategoryRepository(CategoryRepository):
    """Implementación SQLAlchemy del repositorio de categorías"""
    
    def __init__(self):
        self.engine = get_engine()
        self.Session = sessionmaker(bind=self.engine)
    
    def save(self, category: Category) -> Category:
        """Guarda una categoría"""
        session = self.Session()
        try:
            if category.id is None:
                category_model = self._domain_to_model(category)
                session.add(category_model)
                session.flush()
                category.id = category_model.id
                session.commit()
                return category
            else:
                category_model = session.query(CategoryModel).filter_by(id=category.id).first()
                if not category_model:
                    raise ValueError("Category not found")
                self._update_model_from_domain(category_model, category)
                session.commit()
                return category
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_by_id(self, category_id: int) -> Optional[Category]:
        """Busca categoría por ID"""
        session = self.Session()
        try:
            category_model = session.query(CategoryModel).filter_by(id=category_id).first()
            if not category_model:
                return None
            return self._model_to_domain(category_model)
        finally:
            session.close()
    
    def find_all(self) -> List[Category]:
        """Retorna todas las categorías"""
        session = self.Session()
        try:
            category_models = session.query(CategoryModel).order_by(CategoryModel.name).all()
            return [self._model_to_domain(model) for model in category_models]
        finally:
            session.close()
    
    def find_active_categories(self) -> List[Category]:
        """Busca categorías activas"""
        session = self.Session()
        try:
            category_models = session.query(CategoryModel)\
                .filter_by(is_active=True)\
                .order_by(CategoryModel.name).all()
            return [self._model_to_domain(model) for model in category_models]
        finally:
            session.close()
    
    def find_by_name(self, name: str) -> Optional[Category]:
        """Busca categoría por nombre exacto"""
        session = self.Session()
        try:
            category_model = session.query(CategoryModel).filter_by(name=name).first()
            if not category_model:
                return None
            return self._model_to_domain(category_model)
        finally:
            session.close()
    
    def find_by_parent_id(self, parent_id: int) -> List[Category]:
        """Busca categorías hijas de una categoría padre"""
        session = self.Session()
        try:
            category_models = session.query(CategoryModel)\
                .filter_by(parent_id=parent_id)\
                .order_by(CategoryModel.name).all()
            return [self._model_to_domain(model) for model in category_models]
        finally:
            session.close()
    
    def find_root_categories(self) -> List[Category]:
        """Busca categorías raíz (sin padre)"""
        session = self.Session()
        try:
            category_models = session.query(CategoryModel)\
                .filter(CategoryModel.parent_id.is_(None))\
                .order_by(CategoryModel.name).all()
            return [self._model_to_domain(model) for model in category_models]
        finally:
            session.close()
    
    def update(self, category: Category) -> Category:
        """Actualiza una categoría"""
        return self.save(category)
    
    def delete(self, category_id: int) -> bool:
        """Elimina una categoría"""
        session = self.Session()
        try:
            category_model = session.query(CategoryModel).filter_by(id=category_id).first()
            if not category_model:
                return False
            session.delete(category_model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def has_products(self, category_id: int) -> bool:
        """Verifica si una categoría tiene productos asociados"""
        session = self.Session()
        try:
            from infra.database.models import ProductModel
            count = session.query(ProductModel).filter_by(category_id=category_id).count()
            return count > 0
        finally:
            session.close()
    
    def has_subcategories(self, category_id: int) -> bool:
        """Verifica si una categoría tiene subcategorías"""
        session = self.Session()
        try:
            count = session.query(CategoryModel).filter_by(parent_id=category_id).count()
            return count > 0
        finally:
            session.close()
    
    def _domain_to_model(self, category: Category) -> CategoryModel:
        """Convierte entidad de dominio a modelo SQLAlchemy"""
        return CategoryModel(
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            is_active=category.is_active,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    
    def _model_to_domain(self, model: CategoryModel) -> Category:
        """Convierte modelo SQLAlchemy a entidad de dominio"""
        return Category(
            id=model.id,
            name=model.name,
            description=model.description,
            parent_id=model.parent_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _update_model_from_domain(self, model: CategoryModel, category: Category):
        """Actualiza modelo SQLAlchemy desde entidad de dominio"""
        model.name = category.name
        model.description = category.description
        model.parent_id = category.parent_id
        model.is_active = category.is_active
        model.updated_at = category.updated_at