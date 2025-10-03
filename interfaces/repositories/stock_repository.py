"""
EXPLICACIÓN: Interfaz que define las operaciones del repositorio de stock.
Define los contratos para el acceso a datos de inventario y movimientos de stock.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date
from domain.entities.stock import Stock, StockMovement, StockMovementType

class StockRepository(ABC):
    """Interfaz para el repositorio de stock"""
    
    @abstractmethod
    def save_stock(self, stock: Stock) -> Stock:
        """Guarda un registro de stock"""
        pass
    
    @abstractmethod
    def find_stock_by_id(self, stock_id: int) -> Optional[Stock]:
        """Busca stock por ID"""
        pass
    
    @abstractmethod
    def find_stock_by_product_id(self, product_id: int) -> List[Stock]:
        """Busca stock por ID de producto"""
        pass
    
    @abstractmethod
    def find_all_stock(self) -> List[Stock]:
        """Retorna todo el stock"""
        pass
    
    @abstractmethod
    def find_expired_stock(self) -> List[Stock]:
        """Busca stock vencido"""
        pass
    
    @abstractmethod
    def find_near_expiration_stock(self, days_threshold: int = 30) -> List[Stock]:
        """Busca stock próximo a vencer"""
        pass
    
    @abstractmethod
    def find_low_stock(self) -> List[Stock]:
        """Busca productos con stock bajo"""
        pass
    
    @abstractmethod
    def find_stock_by_location(self, location: str) -> List[Stock]:
        """Busca stock por ubicación"""
        pass
    
    @abstractmethod
    def find_stock_by_batch(self, batch_number: str) -> List[Stock]:
        """Busca stock por número de lote"""
        pass
    
    @abstractmethod
    def update_stock(self, stock: Stock) -> Stock:
        """Actualiza un registro de stock"""
        pass
    
    @abstractmethod
    def delete_stock(self, stock_id: int) -> bool:
        """Elimina un registro de stock"""
        pass
    
    @abstractmethod
    def get_total_stock_by_product(self, product_id: int) -> int:
        """Obtiene el stock total de un producto"""
        pass
    
    @abstractmethod
    def get_available_stock_by_product(self, product_id: int) -> int:
        """Obtiene el stock disponible de un producto"""
        pass
    
    # Métodos para movimientos de stock
    @abstractmethod
    def save_movement(self, movement: StockMovement) -> StockMovement:
        """Guarda un movimiento de stock"""
        pass
    
    @abstractmethod
    def find_movement_by_id(self, movement_id: int) -> Optional[StockMovement]:
        """Busca movimiento por ID"""
        pass
    
    @abstractmethod
    def find_movements_by_product_id(self, product_id: int) -> List[StockMovement]:
        """Busca movimientos por ID de producto"""
        pass
    
    @abstractmethod
    def find_movements_by_type(self, movement_type: StockMovementType) -> List[StockMovement]:
        """Busca movimientos por tipo"""
        pass
    
    @abstractmethod
    def find_movements_by_date_range(self, start_date: date, end_date: date) -> List[StockMovement]:
        """Busca movimientos por rango de fechas"""
        pass
    
    @abstractmethod
    def find_movements_by_reference(self, reference_id: int, reference_type: str) -> List[StockMovement]:
        """Busca movimientos por referencia"""
        pass