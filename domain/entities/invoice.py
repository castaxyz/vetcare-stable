"""
EXPLICACIÓN: Entidad que representa una factura en el sistema de facturación.
Contiene las reglas de negocio específicas de una factura y sus elementos.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from enum import Enum

class InvoiceStatus(Enum):
    """Estados posibles de una factura"""
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

@dataclass
class InvoiceItem:
    """
    Elemento individual de una factura.
    Representa un servicio o producto facturado.
    """
    id: Optional[int]
    invoice_id: Optional[int]
    product_id: Optional[int]  # Referencia a producto del inventario
    description: str
    quantity: int
    unit_price: Decimal
    discount_percentage: Decimal = Decimal('0.00')
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de negocio para elementos de factura"""
        if not self.description or len(self.description.strip()) < 3:
            raise ValueError("Description must be at least 3 characters long")
        
        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        
        if self.unit_price < 0:
            raise ValueError("Unit price cannot be negative")
        
        if self.discount_percentage < 0 or self.discount_percentage > 100:
            raise ValueError("Discount percentage must be between 0 and 100")
    
    @property
    def subtotal(self) -> Decimal:
        """Calcula el subtotal sin descuento"""
        return self.unit_price * self.quantity
    
    @property
    def discount_amount(self) -> Decimal:
        """Calcula el monto del descuento"""
        return self.subtotal * (self.discount_percentage / 100)
    
    @property
    def total(self) -> Decimal:
        """Calcula el total con descuento aplicado"""
        return self.subtotal - self.discount_amount

@dataclass
class Invoice:
    """
    Entidad Factura del dominio.
    Representa una factura emitida a un cliente por servicios veterinarios.
    """
    id: Optional[int]
    client_id: int
    appointment_id: Optional[int]  # Puede estar relacionada con una cita
    invoice_number: str
    issue_date: datetime
    due_date: datetime
    status: InvoiceStatus
    tax_percentage: Decimal = Decimal('0.00')
    notes: Optional[str] = None
    items: List[InvoiceItem] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de negocio para facturas"""
        if not self.invoice_number or len(self.invoice_number.strip()) < 3:
            raise ValueError("Invoice number must be at least 3 characters long")

        if self.client_id <= 0:
            raise ValueError("Client ID must be a positive integer")

        # Solo validar fechas si ambas están presentes
        if self.due_date and self.issue_date and self.due_date < self.issue_date:
            raise ValueError("Due date cannot be before issue date")

        if self.tax_percentage < 0 or self.tax_percentage > 100:
            raise ValueError("Tax percentage must be between 0 and 100")
    
    @property
    def subtotal(self) -> Decimal:
        """Calcula el subtotal de todos los elementos"""
        return sum(item.total for item in self.items)
    
    @property
    def tax_amount(self) -> Decimal:
        """Calcula el monto del impuesto"""
        return self.subtotal * (self.tax_percentage / 100)
    
    @property
    def total_amount(self) -> Decimal:
        """Calcula el monto total de la factura"""
        return self.subtotal + self.tax_amount
    
    @property
    def is_overdue(self) -> bool:
        """Verifica si la factura está vencida"""
        return (self.status in [InvoiceStatus.PENDING] and 
                datetime.now() > self.due_date)
    
    def add_item(self, item: InvoiceItem) -> None:
        """Agrega un elemento a la factura"""
        if not isinstance(item, InvoiceItem):
            raise ValueError("Item must be an InvoiceItem instance")
        
        item.invoice_id = self.id
        self.items.append(item)
    
    def remove_item(self, item_id: int) -> bool:
        """Remueve un elemento de la factura"""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                return True
        return False
    
    def mark_as_paid(self) -> None:
        """Marca la factura como pagada"""
        if self.status == InvoiceStatus.CANCELLED:
            raise ValueError("Cannot mark cancelled invoice as paid")
        self.status = InvoiceStatus.PAID
    
    def cancel(self) -> None:
        """Cancela la factura"""
        if self.status == InvoiceStatus.PAID:
            raise ValueError("Cannot cancel paid invoice")
        self.status = InvoiceStatus.CANCELLED