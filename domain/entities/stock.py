"""
EXPLICACIÓN: Entidad que representa el stock de productos en el inventario.
Maneja las reglas de negocio relacionadas con el control de existencias.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from enum import Enum

class StockMovementType(Enum):
    """Tipos de movimientos de stock"""
    PURCHASE = "purchase"      # Compra/Entrada
    SALE = "sale"             # Venta/Salida
    ADJUSTMENT = "adjustment"  # Ajuste de inventario
    RETURN = "return"         # Devolución
    EXPIRED = "expired"       # Producto vencido
    DAMAGED = "damaged"       # Producto dañado

@dataclass
class StockMovement:
    """
    Representa un movimiento de stock (entrada o salida).
    """
    id: Optional[int]
    product_id: int
    movement_type: StockMovementType
    quantity: int  # Positivo para entradas, negativo para salidas
    reference_id: Optional[int]  # ID de referencia (factura, compra, etc.)
    reference_type: Optional[str]  # Tipo de referencia
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[int] = None  # ID del usuario que realizó el movimiento
    
    def __post_init__(self):
        """Validaciones de negocio para movimientos de stock"""
        if self.product_id <= 0:
            raise ValueError("Product ID must be a positive integer")
        
        if self.quantity == 0:
            raise ValueError("Quantity cannot be zero")
        
        # Validar que las salidas sean negativas y las entradas positivas
        if self.movement_type in [StockMovementType.SALE, StockMovementType.EXPIRED, 
                                 StockMovementType.DAMAGED] and self.quantity > 0:
            self.quantity = -abs(self.quantity)
        elif self.movement_type in [StockMovementType.PURCHASE, StockMovementType.RETURN] and self.quantity < 0:
            self.quantity = abs(self.quantity)

@dataclass
class Stock:
    """
    Entidad Stock del dominio.
    Representa el inventario actual de un producto específico.
    """
    id: Optional[int]
    product_id: int
    current_quantity: int
    reserved_quantity: int = 0  # Cantidad reservada para órdenes pendientes
    expiration_date: Optional[date] = None
    batch_number: Optional[str] = None
    location: Optional[str] = None  # Ubicación física en el almacén
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de negocio para stock"""
        if self.product_id <= 0:
            raise ValueError("Product ID must be a positive integer")
        
        if self.current_quantity < 0:
            raise ValueError("Current quantity cannot be negative")
        
        if self.reserved_quantity < 0:
            raise ValueError("Reserved quantity cannot be negative")
        
        if self.reserved_quantity > self.current_quantity:
            raise ValueError("Reserved quantity cannot exceed current quantity")
    
    @property
    def available_quantity(self) -> int:
        """Calcula la cantidad disponible (no reservada)"""
        return self.current_quantity - self.reserved_quantity
    
    @property
    def is_expired(self) -> bool:
        """Verifica si el stock está vencido"""
        if not self.expiration_date:
            return False
        return date.today() > self.expiration_date
    
    @property
    def days_to_expiration(self) -> Optional[int]:
        """Calcula los días hasta el vencimiento"""
        if not self.expiration_date:
            return None
        delta = self.expiration_date - date.today()
        return delta.days
    
    def is_near_expiration(self, days_threshold: int = 30) -> bool:
        """Verifica si el producto está cerca del vencimiento"""
        days_to_exp = self.days_to_expiration
        return days_to_exp is not None and 0 <= days_to_exp <= days_threshold
    
    def add_stock(self, quantity: int) -> None:
        """Agrega stock (entrada)"""
        if quantity <= 0:
            raise ValueError("Quantity to add must be positive")
        self.current_quantity += quantity
        self.last_updated = datetime.now()
    
    def remove_stock(self, quantity: int) -> None:
        """Remueve stock (salida)"""
        if quantity <= 0:
            raise ValueError("Quantity to remove must be positive")
        
        if quantity > self.available_quantity:
            raise ValueError("Cannot remove more stock than available")
        
        self.current_quantity -= quantity
        self.last_updated = datetime.now()
    
    def reserve_stock(self, quantity: int) -> None:
        """Reserva stock para una orden"""
        if quantity <= 0:
            raise ValueError("Quantity to reserve must be positive")
        
        if quantity > self.available_quantity:
            raise ValueError("Cannot reserve more stock than available")
        
        self.reserved_quantity += quantity
    
    def release_reservation(self, quantity: int) -> None:
        """Libera stock reservado"""
        if quantity <= 0:
            raise ValueError("Quantity to release must be positive")
        
        if quantity > self.reserved_quantity:
            raise ValueError("Cannot release more than reserved quantity")
        
        self.reserved_quantity -= quantity