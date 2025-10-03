"""
EXPLICACIÓN: Entidad que representa un producto en el inventario.
Contiene las reglas de negocio específicas de productos veterinarios.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal
from enum import Enum

class ProductStatus(Enum):
    """Estados posibles de un producto"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"

class ProductType(Enum):
    """Tipos de productos"""
    MEDICATION = "medication"
    SUPPLY = "supply"
    EQUIPMENT = "equipment"
    SERVICE = "service"
    FOOD = "food"
    ACCESSORY = "accessory"

@dataclass
class Product:
    """
    Entidad Producto del dominio.
    Representa un producto o servicio disponible en la clínica veterinaria.
    """
    id: Optional[int]
    name: str
    description: Optional[str]
    sku: str  # Stock Keeping Unit - código único del producto
    category_id: Optional[int]
    product_type: ProductType
    unit_price: Decimal
    cost_price: Decimal
    status: ProductStatus = ProductStatus.ACTIVE
    minimum_stock: int = 0
    maximum_stock: Optional[int] = None
    reorder_point: int = 0
    supplier: Optional[str] = None
    expiration_tracking: bool = False  # Si el producto requiere seguimiento de vencimiento
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de negocio para productos"""
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Product name must be at least 2 characters long")
        
        if not self.sku or len(self.sku.strip()) < 3:
            raise ValueError("SKU must be at least 3 characters long")
        
        if self.unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        
        if self.cost_price < 0:
            raise ValueError("Cost price cannot be negative")
        
        if self.minimum_stock < 0:
            raise ValueError("Minimum stock cannot be negative")
        
        if self.maximum_stock is not None and self.maximum_stock < self.minimum_stock:
            raise ValueError("Maximum stock cannot be less than minimum stock")
        
        if self.reorder_point < 0:
            raise ValueError("Reorder point cannot be negative")
    
    @property
    def profit_margin(self) -> Decimal:
        """Calcula el margen de ganancia"""
        if self.cost_price == 0:
            return Decimal('0.00')
        return ((self.unit_price - self.cost_price) / self.cost_price) * 100
    
    @property
    def is_active(self) -> bool:
        """Verifica si el producto está activo"""
        return self.status == ProductStatus.ACTIVE
    
    def deactivate(self) -> None:
        """Desactiva el producto"""
        self.status = ProductStatus.INACTIVE
    
    def activate(self) -> None:
        """Activa el producto"""
        self.status = ProductStatus.ACTIVE
    
    def discontinue(self) -> None:
        """Descontinúa el producto"""
        self.status = ProductStatus.DISCONTINUED