"""
EXPLICACIÓN: Service que maneja la lógica de negocio relacionada con facturación.
Coordina las operaciones CRUD y validaciones de facturas e items de factura.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal

from domain.entities.invoice import Invoice, InvoiceItem, InvoiceStatus
from interfaces.repositories.invoice_repository import InvoiceRepository
from interfaces.repositories.client_repository import ClientRepository
from interfaces.repositories.appointment_repository import AppointmentRepository

class InvoiceService:
    """
    Servicio para gestión de facturación.
    Maneja casos de uso relacionados con facturas y elementos de factura.
    """
    
    def __init__(self, 
                 invoice_repository: InvoiceRepository,
                 client_repository: ClientRepository,
                 appointment_repository: AppointmentRepository):
        self._invoice_repository = invoice_repository
        self._client_repository = client_repository
        self._appointment_repository = appointment_repository
    
    def create_invoice(self, invoice_data: Dict[str, Any]) -> Invoice:
        """
        CASO DE USO: Crear nueva factura
        
        Args:
            invoice_data: Diccionario con datos de la factura
            
        Returns:
            Invoice creada
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        # Validar datos requeridos
        self._validate_invoice_data(invoice_data)
        
        # Verificar que el cliente existe
        client = self._client_repository.find_by_id(invoice_data['client_id'])
        if not client:
            raise ValueError("Client not found")
        
        # Verificar cita si se proporciona
        if invoice_data.get('appointment_id'):
            appointment = self._appointment_repository.find_by_id(invoice_data['appointment_id'])
            if not appointment:
                raise ValueError("Appointment not found")
            
            if appointment.client_id != invoice_data['client_id']:
                raise ValueError("Appointment does not belong to the specified client")
        
        # Generar número de factura si no se proporciona
        if not invoice_data.get('invoice_number'):
            invoice_data['invoice_number'] = self._invoice_repository.get_next_invoice_number()
        
        # Verificar que el número de factura sea único
        existing_invoice = self._invoice_repository.find_by_invoice_number(invoice_data['invoice_number'])
        if existing_invoice:
            raise ValueError("Invoice number already exists")
        
        # Crear la factura
        # Crear la factura
        invoice = Invoice(
            id=None,
            client_id=invoice_data['client_id'],
            appointment_id=invoice_data.get('appointment_id'),
            invoice_number=invoice_data['invoice_number'],
            issue_date=invoice_data.get('issue_date', datetime.now()),
            due_date=invoice_data.get('due_date', datetime.now() + timedelta(days=30)),
            status=invoice_data.get('status', InvoiceStatus.DRAFT),  # Usar el enum directamente
            tax_percentage=Decimal(str(invoice_data.get('tax_percentage', 0))),
            notes=invoice_data.get('notes'),
            created_at=datetime.now()
        )
        
        # Agregar items si se proporcionan
        if invoice_data.get('items'):
            for item_data in invoice_data['items']:
                item = self._create_invoice_item(item_data)
                invoice.add_item(item)
        
        return self._invoice_repository.save(invoice)
    
    def add_item_to_invoice(self, invoice_id: int, item_data: Dict[str, Any]) -> Invoice:
        """
        CASO DE USO: Agregar item a factura existente
        
        Args:
            invoice_id: ID de la factura
            item_data: Datos del item a agregar
            
        Returns:
            Invoice actualizada
        """
        invoice = self._invoice_repository.find_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Cannot modify paid invoice")
        
        if invoice.status == InvoiceStatus.CANCELLED:
            raise ValueError("Cannot modify cancelled invoice")
        
        item = self._create_invoice_item(item_data)
        invoice.add_item(item)
        
        return self._invoice_repository.update(invoice)
    
    def update_invoice_status(self, invoice_id: int, new_status: InvoiceStatus) -> Invoice:
        """
        CASO DE USO: Actualizar estado de factura
        
        Args:
            invoice_id: ID de la factura
            new_status: Nuevo estado
            
        Returns:
            Invoice actualizada
        """
        invoice = self._invoice_repository.find_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        if new_status == InvoiceStatus.PAID:
            invoice.mark_as_paid()
        elif new_status == InvoiceStatus.CANCELLED:
            invoice.cancel()
        else:
            invoice.status = new_status
        
        invoice.updated_at = datetime.now()
        return self._invoice_repository.update(invoice)
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """
        CASO DE USO: Obtener factura por ID
        """
        return self._invoice_repository.find_by_id(invoice_id)
    
    def get_invoices_by_client(self, client_id: int) -> List[Invoice]:
        """
        CASO DE USO: Obtener facturas de un cliente
        """
        return self._invoice_repository.find_by_client_id(client_id)
    
    def get_overdue_invoices(self) -> List[Invoice]:
        """
        CASO DE USO: Obtener facturas vencidas
        """
        return self._invoice_repository.find_overdue_invoices()
    
    def get_revenue_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        CASO DE USO: Generar reporte de ingresos
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Diccionario con datos del reporte
        """
        invoices = self._invoice_repository.find_by_date_range(start_date, end_date)
        paid_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.PAID]
        
        total_revenue = sum(float(inv.total_amount) for inv in paid_invoices)
        total_invoices = len(invoices)
        paid_invoices_count = len(paid_invoices)
        pending_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.PENDING]
        pending_amount = sum(float(inv.total_amount) for inv in pending_invoices)
        
        return {
            'period': {'start_date': start_date, 'end_date': end_date},
            'total_revenue': total_revenue,
            'total_invoices': total_invoices,
            'paid_invoices': paid_invoices_count,
            'pending_invoices': len(pending_invoices),
            'pending_amount': pending_amount,
            'collection_rate': (paid_invoices_count / total_invoices * 100) if total_invoices > 0 else 0
        }

    def get_all_invoices(self) -> List[Invoice]:
        """
        CASO DE USO: Obtener todas las facturas

        Returns:
            Lista de todas las facturas
        """
        return self._invoice_repository.find_all()

    def get_invoices_by_status(self, status: InvoiceStatus) -> List[Invoice]:
        """
        CASO DE USO: Obtener facturas por estado

        Args:
            status: Estado de las facturas a buscar

        Returns:
            Lista de facturas con el estado especificado
        """
        return self._invoice_repository.find_by_status(status)

    def _create_invoice_item(self, item_data: Dict[str, Any]) -> InvoiceItem:
        """Crea un item de factura a partir de los datos proporcionados"""
        return InvoiceItem(
            id=None,
            invoice_id=None,
            product_id=item_data.get('product_id'),
            description=item_data['description'],
            quantity=item_data['quantity'],
            unit_price=Decimal(str(item_data['unit_price'])),
            discount_percentage=Decimal(str(item_data.get('discount_percentage', 0))),
            created_at=datetime.now()
        )

    def _validate_invoice_data(self, invoice_data: Dict[str, Any]) -> None:
        """Valida los datos de la factura"""
        required_fields = ['client_id']

        for field in required_fields:
            if field not in invoice_data or invoice_data[field] is None:
                raise ValueError(f"Field '{field}' is required")

        if invoice_data['client_id'] <= 0:
            raise ValueError("Client ID must be a positive integer")

        if invoice_data.get('tax_percentage') is not None:
            tax_percentage = float(invoice_data['tax_percentage'])
            if tax_percentage < 0 or tax_percentage > 100:
                raise ValueError("Tax percentage must be between 0 and 100")