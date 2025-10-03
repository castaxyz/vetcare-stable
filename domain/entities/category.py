"""
EXPLICACIÓN: Entidad que representa una categoría de productos en el inventario.
Permite organizar y clasificar los productos de manera jerárquica.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Category:
    """
    Entidad Categoría del dominio.
    Representa una categoría para organizar productos en el inventario.
    """
    id: Optional[int]
    name: str
    description: Optional[str]
    parent_id: Optional[int] = None  # Para categorías jerárquicas
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de negocio para categorías"""
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Category name must be at least 2 characters long")
        
        # Evitar auto-referencia
        if self.parent_id is not None and self.parent_id == self.id:
            raise ValueError("Category cannot be its own parent")
    
    @property
    def is_root_category(self) -> bool:
        """Verifica si es una categoría raíz (sin padre)"""
        return self.parent_id is None
    
    @property
    def has_parent(self) -> bool:
        """Verifica si tiene categoría padre"""
        return self.parent_id is not None
    
    def deactivate(self) -> None:
        """Desactiva la categoría"""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def activate(self) -> None:
        """Activa la categoría"""
        self.is_active = True
        self.updated_at = datetime.now()