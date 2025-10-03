"""
EXPLICACIÓN: Interfaz que define las operaciones del repositorio de facturas.
Define los contratos para el acceso a datos de facturación.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, date
from domain.entities.invoice import Invoice, InvoiceStatus

class InvoiceRepository(ABC):
    """Interfaz para el repositorio de facturas"""
    
    @abstractmethod
    def save(self, invoice: Invoice) -> Invoice:
        """Guarda una factura"""
        pass
    
    @abstractmethod
    def find_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Busca factura por ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Invoice]:
        """Retorna todas las facturas"""
        pass
    
    @abstractmethod
    def find_by_client_id(self, client_id: int) -> List[Invoice]:
        """Busca facturas por ID de cliente"""
        pass
    
    @abstractmethod
    def find_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Busca factura por número de factura"""
        pass
    
    @abstractmethod
    def find_by_status(self, status: InvoiceStatus) -> List[Invoice]:
        """Busca facturas por estado"""
        pass
    
    @abstractmethod
    def find_by_date_range(self, start_date: date, end_date: date) -> List[Invoice]:
        """Busca facturas por rango de fechas"""
        pass
    
    @abstractmethod
    def find_overdue_invoices(self) -> List[Invoice]:
        """Busca facturas vencidas"""
        pass
    
    @abstractmethod
    def find_by_appointment_id(self, appointment_id: int) -> List[Invoice]:
        """Busca facturas por ID de cita"""
        pass
    
    @abstractmethod
    def update(self, invoice: Invoice) -> Invoice:
        """Actualiza una factura"""
        pass
    
    @abstractmethod
    def delete(self, invoice_id: int) -> bool:
        """Elimina una factura"""
        pass
    
    @abstractmethod
    def get_next_invoice_number(self) -> str:
        """Genera el siguiente número de factura"""
        pass
    
    @abstractmethod
    def get_revenue_by_period(self, start_date: date, end_date: date) -> float:
        """Calcula los ingresos por período"""
        pass