"""
EXPLICACIÓN: Implementación SQLAlchemy del repositorio de facturas.
Maneja la persistencia de facturas usando SQLAlchemy ORM.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import and_, or_

from interfaces.repositories.invoice_repository import InvoiceRepository
from domain.entities.invoice import Invoice, InvoiceItem, InvoiceStatus
from infra.database.models import InvoiceModel, InvoiceItemModel, Base
from infra.database.connection import get_engine

class SQLInvoiceRepository(InvoiceRepository):
    """Implementación SQLAlchemy del repositorio de facturas"""
    
    def __init__(self):
        self.engine = get_engine()
        self.Session = sessionmaker(bind=self.engine)
    
    def save(self, invoice: Invoice) -> Invoice:
        """Guarda una factura"""
        session = self.Session()
        try:
            if invoice.id is None:
                # Crear nueva factura
                invoice_model = self._domain_to_model(invoice)
                session.add(invoice_model)
                session.flush()  # Para obtener el ID
                invoice.id = invoice_model.id
                
                # Agregar items
                for item in invoice.items:
                    item.invoice_id = invoice.id
                    item_model = self._item_domain_to_model(item)
                    session.add(item_model)
                
                session.commit()
                return invoice
            else:
                # Actualizar factura existente
                invoice_model = session.query(InvoiceModel).filter_by(id=invoice.id).first()
                if not invoice_model:
                    raise ValueError("Invoice not found")
                
                self._update_model_from_domain(invoice_model, invoice)
                session.commit()
                return invoice
                
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Busca factura por ID"""
        session = self.Session()
        try:
            invoice_model = session.query(InvoiceModel)\
                .options(joinedload(InvoiceModel.items))\
                .filter_by(id=invoice_id).first()
            
            if not invoice_model:
                return None
            
            return self._model_to_domain(invoice_model)
        finally:
            session.close()
    
    def find_all(self) -> List[Invoice]:
        """Retorna todas las facturas"""
        session = self.Session()
        try:
            invoice_models = session.query(InvoiceModel)\
                .options(joinedload(InvoiceModel.items))\
                .order_by(InvoiceModel.created_at.desc()).all()
            
            return [self._model_to_domain(model) for model in invoice_models]
        finally:
            session.close()
    
    def find_by_client_id(self, client_id: int) -> List[Invoice]:
        """Busca facturas por ID de cliente"""
        session = self.Session()
        try:
            invoice_models = session.query(InvoiceModel)\
                .options(joinedload(InvoiceModel.items))\
                .filter_by(client_id=client_id)\
                .order_by(InvoiceModel.created_at.desc()).all()
            
            return [self._model_to_domain(model) for model in invoice_models]
        finally:
            session.close()
    
    def find_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Busca factura por número de factura"""
        session = self.Session()
        try:
            invoice_model = session.query(InvoiceModel)\
                .options(joinedload(InvoiceModel.items))\
                .filter_by(invoice_number=invoice_number).first()
            
            if not invoice_model:
                return None
            
            return self._model_to_domain(invoice_model)
        finally:
            session.close()
    
    def find_by_status(self, status: InvoiceStatus) -> List[Invoice]:
        """Busca facturas por estado"""
        session = self.Session()
        try:
            invoice_models = session.query(InvoiceModel)\
                .options(joinedload(InvoiceModel.items))\
                .filter_by(status=status.value)\
                .order_by(InvoiceModel.created_at.desc()).all()

            return [self._model_to_domain(model) for model in invoice_models]
        finally:
            session.close()
    
    def find_by_date_range(self, start_date: date, end_date: date) -> List[Invoice]:
        """Busca facturas por rango de fechas"""
        session = self.Session()
        try:
            invoice_models = session.query(InvoiceModel)\
                .options(joinedload(InvoiceModel.items))\
                .filter(and_(
                    InvoiceModel.issue_date >= start_date,
                    InvoiceModel.issue_date <= end_date
                ))\
                .order_by(InvoiceModel.issue_date.desc()).all()
            
            return [self._model_to_domain(model) for model in invoice_models]
        finally:
            session.close()
    
    def find_overdue_invoices(self) -> List[Invoice]:
        """Busca facturas vencidas"""
        session = self.Session()
        try:
            from datetime import datetime
            invoice_models = session.query(InvoiceModel)\
                .options(joinedload(InvoiceModel.items))\
                .filter(and_(
                    InvoiceModel.status == InvoiceStatus.PENDING.value,
                    InvoiceModel.due_date < datetime.now().date()
                ))\
                .order_by(InvoiceModel.due_date.asc()).all()

            return [self._model_to_domain(model) for model in invoice_models]
        finally:
            session.close()
    
    def find_by_appointment_id(self, appointment_id: int) -> List[Invoice]:
        """Busca facturas por ID de cita"""
        session = self.Session()
        try:
            invoice_models = session.query(InvoiceModel)\
                .options(joinedload(InvoiceModel.items))\
                .filter_by(appointment_id=appointment_id)\
                .order_by(InvoiceModel.created_at.desc()).all()
            
            return [self._model_to_domain(model) for model in invoice_models]
        finally:
            session.close()
    
    def update(self, invoice: Invoice) -> Invoice:
        """Actualiza una factura"""
        return self.save(invoice)
    
    def delete(self, invoice_id: int) -> bool:
        """Elimina una factura"""
        session = self.Session()
        try:
            invoice_model = session.query(InvoiceModel).filter_by(id=invoice_id).first()
            if not invoice_model:
                return False
            
            session.delete(invoice_model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_next_invoice_number(self) -> str:
        """Genera el siguiente número de factura"""
        session = self.Session()
        try:
            from datetime import datetime
            year = datetime.now().year
            
            # Buscar el último número de factura del año
            last_invoice = session.query(InvoiceModel)\
                .filter(InvoiceModel.invoice_number.like(f'{year}-%'))\
                .order_by(InvoiceModel.invoice_number.desc()).first()
            
            if last_invoice:
                # Extraer el número secuencial
                parts = last_invoice.invoice_number.split('-')
                if len(parts) == 2:
                    try:
                        last_number = int(parts[1])
                        next_number = last_number + 1
                    except ValueError:
                        next_number = 1
                else:
                    next_number = 1
            else:
                next_number = 1
            
            return f"{year}-{next_number:06d}"
        finally:
            session.close()
    
    def get_revenue_by_period(self, start_date: date, end_date: date) -> float:
        """Calcula los ingresos por período"""
        session = self.Session()
        try:
            from sqlalchemy import func
            result = session.query(func.sum(
                InvoiceItemModel.quantity * InvoiceItemModel.unit_price * 
                (1 - InvoiceItemModel.discount_percentage / 100)
            )).join(InvoiceModel).filter(and_(
                InvoiceModel.status == InvoiceStatus.PAID,
                InvoiceModel.issue_date >= start_date,
                InvoiceModel.issue_date <= end_date
            )).scalar()
            
            return float(result or 0)
        finally:
            session.close()
    
    def _domain_to_model(self, invoice: Invoice) -> InvoiceModel:
        """Convierte entidad de dominio a modelo SQLAlchemy"""
        return InvoiceModel(
            client_id=invoice.client_id,
            appointment_id=invoice.appointment_id,
            invoice_number=invoice.invoice_number,
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            status=invoice.status,
            tax_percentage=invoice.tax_percentage,
            notes=invoice.notes,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at
        )
    
    def _item_domain_to_model(self, item: InvoiceItem) -> InvoiceItemModel:
        """Convierte item de dominio a modelo SQLAlchemy"""
        return InvoiceItemModel(
            invoice_id=item.invoice_id,
            product_id=item.product_id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_percentage=item.discount_percentage,
            created_at=item.created_at
        )
    
    def _model_to_domain(self, model: InvoiceModel) -> Invoice:
        """Convierte modelo SQLAlchemy a entidad de dominio"""
        items = [self._item_model_to_domain(item) for item in model.items]
        
        invoice = Invoice(
            id=model.id,
            client_id=model.client_id,
            appointment_id=model.appointment_id,
            invoice_number=model.invoice_number,
            issue_date=model.issue_date,
            due_date=model.due_date,
            status=model.status,
            tax_percentage=model.tax_percentage,
            notes=model.notes,
            items=items,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
        
        return invoice
    
    def _item_model_to_domain(self, model: InvoiceItemModel) -> InvoiceItem:
        """Convierte modelo de item SQLAlchemy a entidad de dominio"""
        return InvoiceItem(
            id=model.id,
            invoice_id=model.invoice_id,
            product_id=model.product_id,
            description=model.description,
            quantity=model.quantity,
            unit_price=model.unit_price,
            discount_percentage=model.discount_percentage,
            created_at=model.created_at
        )
    
    def _update_model_from_domain(self, model: InvoiceModel, invoice: Invoice):
        """Actualiza modelo SQLAlchemy desde entidad de dominio"""
        model.client_id = invoice.client_id
        model.appointment_id = invoice.appointment_id
        model.invoice_number = invoice.invoice_number
        model.issue_date = invoice.issue_date
        model.due_date = invoice.due_date
        model.status = invoice.status
        model.tax_percentage = invoice.tax_percentage
        model.notes = invoice.notes
        model.updated_at = invoice.updated_at