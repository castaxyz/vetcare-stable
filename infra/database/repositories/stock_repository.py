"""
EXPLICACIÓN: Implementación básica SQLAlchemy del repositorio de stock.
Versión simplificada para funcionalidad básica.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import sessionmaker

from interfaces.repositories.stock_repository import StockRepository
from domain.entities.stock import Stock, StockMovement, StockMovementType
from infra.database.models import StockModel, StockMovementModel
from infra.database.connection import get_engine

class SQLStockRepository(StockRepository):
    """Implementación SQLAlchemy del repositorio de stock"""
    
    def __init__(self):
        self.engine = get_engine()
        self.Session = sessionmaker(bind=self.engine)
    
    def save_stock(self, stock: Stock) -> Stock:
        """Guarda un registro de stock"""
        session = self.Session()
        try:
            if stock.id is None:
                stock_model = self._stock_domain_to_model(stock)
                session.add(stock_model)
                session.flush()
                stock.id = stock_model.id
                session.commit()
                return stock
            else:
                stock_model = session.query(StockModel).filter_by(id=stock.id).first()
                if not stock_model:
                    raise ValueError("Stock not found")
                self._update_stock_model_from_domain(stock_model, stock)
                session.commit()
                return stock
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_stock_by_id(self, stock_id: int) -> Optional[Stock]:
        """Busca stock por ID"""
        session = self.Session()
        try:
            stock_model = session.query(StockModel).filter_by(id=stock_id).first()
            if not stock_model:
                return None
            return self._stock_model_to_domain(stock_model)
        finally:
            session.close()
    
    def find_stock_by_product_id(self, product_id: int) -> List[Stock]:
        """Busca stock por ID de producto"""
        session = self.Session()
        try:
            stock_models = session.query(StockModel).filter_by(product_id=product_id).all()
            return [self._stock_model_to_domain(model) for model in stock_models]
        finally:
            session.close()
    
    def find_all_stock(self) -> List[Stock]:
        """Retorna todo el stock"""
        session = self.Session()
        try:
            stock_models = session.query(StockModel).all()
            return [self._stock_model_to_domain(model) for model in stock_models]
        finally:
            session.close()
    
    def find_expired_stock(self) -> List[Stock]:
        """Busca stock vencido"""
        session = self.Session()
        try:
            today = date.today()
            stock_models = session.query(StockModel)\
                .filter(StockModel.expiration_date < today).all()
            return [self._stock_model_to_domain(model) for model in stock_models]
        finally:
            session.close()
    
    def find_near_expiration_stock(self, days_threshold: int = 30) -> List[Stock]:
        """Busca stock próximo a vencer"""
        session = self.Session()
        try:
            from datetime import timedelta
            threshold_date = date.today() + timedelta(days=days_threshold)
            stock_models = session.query(StockModel)\
                .filter(StockModel.expiration_date <= threshold_date)\
                .filter(StockModel.expiration_date >= date.today()).all()
            return [self._stock_model_to_domain(model) for model in stock_models]
        finally:
            session.close()
    
    def find_low_stock(self) -> List[Stock]:
        """Busca productos con stock bajo"""
        # Implementación básica
        return []
    
    def find_stock_by_location(self, location: str) -> List[Stock]:
        """Busca stock por ubicación"""
        session = self.Session()
        try:
            stock_models = session.query(StockModel)\
                .filter(StockModel.location.ilike(f'%{location}%')).all()
            return [self._stock_model_to_domain(model) for model in stock_models]
        finally:
            session.close()
    
    def find_stock_by_batch(self, batch_number: str) -> List[Stock]:
        """Busca stock por número de lote"""
        session = self.Session()
        try:
            stock_models = session.query(StockModel)\
                .filter_by(batch_number=batch_number).all()
            return [self._stock_model_to_domain(model) for model in stock_models]
        finally:
            session.close()
    
    def update_stock(self, stock: Stock) -> Stock:
        """Actualiza un registro de stock"""
        return self.save_stock(stock)
    
    def delete_stock(self, stock_id: int) -> bool:
        """Elimina un registro de stock"""
        session = self.Session()
        try:
            stock_model = session.query(StockModel).filter_by(id=stock_id).first()
            if not stock_model:
                return False
            session.delete(stock_model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_total_stock_by_product(self, product_id: int) -> int:
        """Obtiene el stock total de un producto"""
        session = self.Session()
        try:
            from sqlalchemy import func
            result = session.query(func.sum(StockModel.current_quantity))\
                .filter_by(product_id=product_id).scalar()
            return int(result or 0)
        finally:
            session.close()
    
    def get_available_stock_by_product(self, product_id: int) -> int:
        """Obtiene el stock disponible de un producto"""
        session = self.Session()
        try:
            from sqlalchemy import func
            result = session.query(func.sum(StockModel.current_quantity - StockModel.reserved_quantity))\
                .filter_by(product_id=product_id).scalar()
            return int(result or 0)
        finally:
            session.close()
    
    # Métodos para movimientos de stock
    def save_movement(self, movement: StockMovement) -> StockMovement:
        """Guarda un movimiento de stock"""
        session = self.Session()
        try:
            movement_model = self._movement_domain_to_model(movement)
            session.add(movement_model)
            session.flush()
            movement.id = movement_model.id
            session.commit()
            return movement
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_movement_by_id(self, movement_id: int) -> Optional[StockMovement]:
        """Busca movimiento por ID"""
        session = self.Session()
        try:
            movement_model = session.query(StockMovementModel).filter_by(id=movement_id).first()
            if not movement_model:
                return None
            return self._movement_model_to_domain(movement_model)
        finally:
            session.close()
    
    def find_movements_by_product_id(self, product_id: int) -> List[StockMovement]:
        """Busca movimientos por ID de producto"""
        session = self.Session()
        try:
            movement_models = session.query(StockMovementModel)\
                .filter_by(product_id=product_id)\
                .order_by(StockMovementModel.created_at.desc()).all()
            return [self._movement_model_to_domain(model) for model in movement_models]
        finally:
            session.close()
    
    def find_movements_by_type(self, movement_type: StockMovementType) -> List[StockMovement]:
        """Busca movimientos por tipo"""
        session = self.Session()
        try:
            movement_models = session.query(StockMovementModel)\
                .filter_by(movement_type=movement_type).all()
            return [self._movement_model_to_domain(model) for model in movement_models]
        finally:
            session.close()
    
    def find_movements_by_date_range(self, start_date: date, end_date: date) -> List[StockMovement]:
        """Busca movimientos por rango de fechas"""
        session = self.Session()
        try:
            from sqlalchemy import and_
            movement_models = session.query(StockMovementModel)\
                .filter(and_(
                    StockMovementModel.created_at >= start_date,
                    StockMovementModel.created_at <= end_date
                )).all()
            return [self._movement_model_to_domain(model) for model in movement_models]
        finally:
            session.close()
    
    def find_movements_by_reference(self, reference_id: int, reference_type: str) -> List[StockMovement]:
        """Busca movimientos por referencia"""
        session = self.Session()
        try:
            movement_models = session.query(StockMovementModel)\
                .filter_by(reference_id=reference_id, reference_type=reference_type).all()
            return [self._movement_model_to_domain(model) for model in movement_models]
        finally:
            session.close()
    
    def _stock_domain_to_model(self, stock: Stock) -> StockModel:
        """Convierte entidad de stock de dominio a modelo SQLAlchemy"""
        return StockModel(
            product_id=stock.product_id,
            current_quantity=stock.current_quantity,
            reserved_quantity=stock.reserved_quantity,
            expiration_date=stock.expiration_date,
            batch_number=stock.batch_number,
            location=stock.location,
            last_updated=stock.last_updated
        )
    
    def _stock_model_to_domain(self, model: StockModel) -> Stock:
        """Convierte modelo SQLAlchemy a entidad de stock de dominio"""
        return Stock(
            id=model.id,
            product_id=model.product_id,
            current_quantity=model.current_quantity,
            reserved_quantity=model.reserved_quantity,
            expiration_date=model.expiration_date,
            batch_number=model.batch_number,
            location=model.location,
            last_updated=model.last_updated
        )
    
    def _movement_domain_to_model(self, movement: StockMovement) -> StockMovementModel:
        """Convierte entidad de movimiento de dominio a modelo SQLAlchemy"""
        return StockMovementModel(
            product_id=movement.product_id,
            movement_type=movement.movement_type,
            quantity=movement.quantity,
            reference_id=movement.reference_id,
            reference_type=movement.reference_type,
            notes=movement.notes,
            created_at=movement.created_at,
            created_by=movement.created_by
        )
    
    def _movement_model_to_domain(self, model: StockMovementModel) -> StockMovement:
        """Convierte modelo SQLAlchemy a entidad de movimiento de dominio"""
        return StockMovement(
            id=model.id,
            product_id=model.product_id,
            movement_type=model.movement_type,
            quantity=model.quantity,
            reference_id=model.reference_id,
            reference_type=model.reference_type,
            notes=model.notes,
            created_at=model.created_at,
            created_by=model.created_by
        )
    
    def _update_stock_model_from_domain(self, model: StockModel, stock: Stock):
        """Actualiza modelo SQLAlchemy desde entidad de stock de dominio"""
        model.product_id = stock.product_id
        model.current_quantity = stock.current_quantity
        model.reserved_quantity = stock.reserved_quantity
        model.expiration_date = stock.expiration_date
        model.batch_number = stock.batch_number
        model.location = stock.location
        model.last_updated = stock.last_updated