"""
EXPLICACIÓN: Interfaz que define las operaciones del repositorio de categorías.
Define los contratos para el acceso a datos de categorías de productos.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.category import Category

class CategoryRepository(ABC):
    """Interfaz para el repositorio de categorías"""
    
    @abstractmethod
    def save(self, category: Category) -> Category:
        """Guarda una categoría"""
        pass
    
    @abstractmethod
    def find_by_id(self, category_id: int) -> Optional[Category]:
        """Busca categoría por ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Category]:
        """Retorna todas las categorías"""
        pass
    
    @abstractmethod
    def find_active_categories(self) -> List[Category]:
        """Busca categorías activas"""
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Category]:
        """Busca categoría por nombre exacto"""
        pass
    
    @abstractmethod
    def find_by_parent_id(self, parent_id: int) -> List[Category]:
        """Busca categorías hijas de una categoría padre"""
        pass
    
    @abstractmethod
    def find_root_categories(self) -> List[Category]:
        """Busca categorías raíz (sin padre)"""
        pass
    
    @abstractmethod
    def update(self, category: Category) -> Category:
        """Actualiza una categoría"""
        pass
    
    @abstractmethod
    def delete(self, category_id: int) -> bool:
        """Elimina una categoría"""
        pass
    
    @abstractmethod
    def has_products(self, category_id: int) -> bool:
        """Verifica si una categoría tiene productos asociados"""
        pass
    
    @abstractmethod
    def has_subcategories(self, category_id: int) -> bool:
        """Verifica si una categoría tiene subcategorías"""
        pass