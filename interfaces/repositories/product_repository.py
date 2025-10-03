"""
EXPLICACIÓN: Interfaz que define las operaciones del repositorio de productos.
Define los contratos para el acceso a datos de productos del inventario.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.product import Product, ProductStatus, ProductType

class ProductRepository(ABC):
    """Interfaz para el repositorio de productos"""
    
    @abstractmethod
    def save(self, product: Product) -> Product:
        """Guarda un producto"""
        pass
    
    @abstractmethod
    def find_by_id(self, product_id: int) -> Optional[Product]:
        """Busca producto por ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Product]:
        """Retorna todos los productos"""
        pass
    
    @abstractmethod
    def find_by_sku(self, sku: str) -> Optional[Product]:
        """Busca producto por SKU"""
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> List[Product]:
        """Busca productos por nombre (búsqueda parcial)"""
        pass
    
    @abstractmethod
    def find_by_category_id(self, category_id: int) -> List[Product]:
        """Busca productos por categoría"""
        pass
    
    @abstractmethod
    def find_by_type(self, product_type: ProductType) -> List[Product]:
        """Busca productos por tipo"""
        pass
    
    @abstractmethod
    def find_by_status(self, status: ProductStatus) -> List[Product]:
        """Busca productos por estado"""
        pass
    
    @abstractmethod
    def find_active_products(self) -> List[Product]:
        """Busca productos activos"""
        pass
    
    @abstractmethod
    def find_by_supplier(self, supplier: str) -> List[Product]:
        """Busca productos por proveedor"""
        pass
    
    @abstractmethod
    def find_low_stock_products(self) -> List[Product]:
        """Busca productos con stock bajo (por debajo del punto de reorden)"""
        pass
    
    @abstractmethod
    def update(self, product: Product) -> Product:
        """Actualiza un producto"""
        pass
    
    @abstractmethod
    def delete(self, product_id: int) -> bool:
        """Elimina un producto"""
        pass