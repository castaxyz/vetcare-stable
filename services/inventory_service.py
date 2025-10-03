"""
EXPLICACIÓN: Service que maneja la lógica de negocio relacionada con inventario y stock.
Coordina las operaciones de control de stock, movimientos y alertas de inventario.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date

from domain.entities.stock import Stock, StockMovement, StockMovementType
from domain.entities.product import Product
from interfaces.repositories.stock_repository import StockRepository
from interfaces.repositories.product_repository import ProductRepository

class InventoryService:
    """
    Servicio para gestión de inventario.
    Maneja casos de uso relacionados con stock y movimientos de inventario.
    """
    
    def __init__(self, 
                 stock_repository: StockRepository,
                 product_repository: ProductRepository):
        self._stock_repository = stock_repository
        self._product_repository = product_repository
    
    def add_stock(self, product_id: int, quantity: int, 
                  expiration_date: Optional[date] = None,
                  batch_number: Optional[str] = None,
                  location: Optional[str] = None,
                  reference_id: Optional[int] = None,
                  reference_type: Optional[str] = None,
                  notes: Optional[str] = None) -> Stock:
        """
        CASO DE USO: Agregar stock (entrada de inventario)
        
        Args:
            product_id: ID del producto
            quantity: Cantidad a agregar
            expiration_date: Fecha de vencimiento (opcional)
            batch_number: Número de lote (opcional)
            location: Ubicación en almacén (opcional)
            reference_id: ID de referencia (compra, etc.)
            reference_type: Tipo de referencia
            notes: Notas adicionales
            
        Returns:
            Stock actualizado o creado
        """
        # Verificar que el producto existe
        product = self._product_repository.find_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        if not product.is_active:
            raise ValueError("Cannot add stock to inactive product")
        
        # Buscar stock existente para el mismo producto, lote y ubicación
        existing_stocks = self._stock_repository.find_stock_by_product_id(product_id)
        matching_stock = None
        
        for stock in existing_stocks:
            if (stock.batch_number == batch_number and 
                stock.location == location and
                stock.expiration_date == expiration_date):
                matching_stock = stock
                break
        
        if matching_stock:
            # Actualizar stock existente
            matching_stock.add_stock(quantity)
            stock = self._stock_repository.update_stock(matching_stock)
        else:
            # Crear nuevo registro de stock
            stock = Stock(
                id=None,
                product_id=product_id,
                current_quantity=quantity,
                expiration_date=expiration_date,
                batch_number=batch_number,
                location=location,
                last_updated=datetime.now()
            )
            stock = self._stock_repository.save_stock(stock)
        
        # Registrar movimiento
        movement = StockMovement(
            id=None,
            product_id=product_id,
            movement_type=StockMovementType.PURCHASE,
            quantity=quantity,
            reference_id=reference_id,
            reference_type=reference_type,
            notes=notes,
            created_at=datetime.now()
        )
        self._stock_repository.save_movement(movement)
        
        return stock
    
    def remove_stock(self, product_id: int, quantity: int,
                     reference_id: Optional[int] = None,
                     reference_type: Optional[str] = None,
                     notes: Optional[str] = None,
                     movement_type: StockMovementType = StockMovementType.SALE) -> List[Stock]:
        """
        CASO DE USO: Remover stock (salida de inventario)
        
        Args:
            product_id: ID del producto
            quantity: Cantidad a remover
            reference_id: ID de referencia (venta, etc.)
            reference_type: Tipo de referencia
            notes: Notas adicionales
            movement_type: Tipo de movimiento
            
        Returns:
            Lista de stocks afectados
        """
        # Verificar que el producto existe
        product = self._product_repository.find_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        # Obtener stock disponible
        available_stock = self._stock_repository.get_available_stock_by_product(product_id)
        if available_stock < quantity:
            raise ValueError(f"Insufficient stock. Available: {available_stock}, Requested: {quantity}")
        
        # Obtener stocks del producto ordenados por fecha de vencimiento (FIFO)
        stocks = self._stock_repository.find_stock_by_product_id(product_id)
        stocks = [s for s in stocks if s.available_quantity > 0]
        stocks.sort(key=lambda x: x.expiration_date or date.max)
        
        remaining_quantity = quantity
        affected_stocks = []
        
        for stock in stocks:
            if remaining_quantity <= 0:
                break
            
            available_in_stock = stock.available_quantity
            quantity_to_remove = min(remaining_quantity, available_in_stock)
            
            stock.remove_stock(quantity_to_remove)
            self._stock_repository.update_stock(stock)
            affected_stocks.append(stock)
            
            remaining_quantity -= quantity_to_remove
        
        # Registrar movimiento
        movement = StockMovement(
            id=None,
            product_id=product_id,
            movement_type=movement_type,
            quantity=-quantity,  # Negativo para salidas
            reference_id=reference_id,
            reference_type=reference_type,
            notes=notes,
            created_at=datetime.now()
        )
        self._stock_repository.save_movement(movement)
        
        return affected_stocks
    
    def reserve_stock(self, product_id: int, quantity: int) -> List[Stock]:
        """
        CASO DE USO: Reservar stock para una orden
        """
        available_stock = self._stock_repository.get_available_stock_by_product(product_id)
        if available_stock < quantity:
            raise ValueError(f"Insufficient stock to reserve. Available: {available_stock}, Requested: {quantity}")
        
        stocks = self._stock_repository.find_stock_by_product_id(product_id)
        stocks = [s for s in stocks if s.available_quantity > 0]
        stocks.sort(key=lambda x: x.expiration_date or date.max)
        
        remaining_quantity = quantity
        affected_stocks = []
        
        for stock in stocks:
            if remaining_quantity <= 0:
                break
            
            available_in_stock = stock.available_quantity
            quantity_to_reserve = min(remaining_quantity, available_in_stock)
            
            stock.reserve_stock(quantity_to_reserve)
            self._stock_repository.update_stock(stock)
            affected_stocks.append(stock)
            
            remaining_quantity -= quantity_to_reserve
        
        return affected_stocks
    
    def release_reservation(self, product_id: int, quantity: int) -> List[Stock]:
        """
        CASO DE USO: Liberar stock reservado
        """
        stocks = self._stock_repository.find_stock_by_product_id(product_id)
        stocks = [s for s in stocks if s.reserved_quantity > 0]
        
        remaining_quantity = quantity
        affected_stocks = []
        
        for stock in stocks:
            if remaining_quantity <= 0:
                break
            
            reserved_in_stock = stock.reserved_quantity
            quantity_to_release = min(remaining_quantity, reserved_in_stock)
            
            stock.release_reservation(quantity_to_release)
            self._stock_repository.update_stock(stock)
            affected_stocks.append(stock)
            
            remaining_quantity -= quantity_to_release
        
        return affected_stocks
    
    def adjust_stock(self, product_id: int, new_quantity: int, 
                     reason: str, user_id: Optional[int] = None) -> Stock:
        """
        CASO DE USO: Ajustar stock (corrección de inventario)
        """
        current_stock = self._stock_repository.get_total_stock_by_product(product_id)
        difference = new_quantity - current_stock
        
        if difference == 0:
            raise ValueError("No adjustment needed, quantities are equal")
        
        # Crear movimiento de ajuste
        movement = StockMovement(
            id=None,
            product_id=product_id,
            movement_type=StockMovementType.ADJUSTMENT,
            quantity=difference,
            notes=f"Stock adjustment: {reason}",
            created_at=datetime.now(),
            created_by=user_id
        )
        self._stock_repository.save_movement(movement)
        
        # Ajustar el stock principal
        stocks = self._stock_repository.find_stock_by_product_id(product_id)
        if stocks:
            main_stock = stocks[0]  # Usar el primer stock encontrado
            main_stock.current_quantity = new_quantity
            main_stock.last_updated = datetime.now()
            return self._stock_repository.update_stock(main_stock)
        else:
            # Crear nuevo stock si no existe
            stock = Stock(
                id=None,
                product_id=product_id,
                current_quantity=new_quantity,
                last_updated=datetime.now()
            )
            return self._stock_repository.save_stock(stock)
    
    def get_stock_by_product(self, product_id: int) -> List[Stock]:
        """
        CASO DE USO: Obtener stock de un producto
        """
        return self._stock_repository.find_stock_by_product_id(product_id)
    
    def get_low_stock_alerts(self) -> List[Dict[str, Any]]:
        """
        CASO DE USO: Obtener alertas de stock bajo
        """
        low_stock_products = self._product_repository.find_low_stock_products()
        alerts = []
        
        for product in low_stock_products:
            current_stock = self._stock_repository.get_total_stock_by_product(product.id)
            alerts.append({
                'product': product,
                'current_stock': current_stock,
                'minimum_stock': product.minimum_stock,
                'reorder_point': product.reorder_point,
                'alert_level': 'critical' if current_stock == 0 else 'warning'
            })
        
        return alerts
    
    def get_expiration_alerts(self, days_threshold: int = 30) -> List[Dict[str, Any]]:
        """
        CASO DE USO: Obtener alertas de productos próximos a vencer
        """
        near_expiration_stocks = self._stock_repository.find_near_expiration_stock(days_threshold)
        alerts = []
        
        for stock in near_expiration_stocks:
            product = self._product_repository.find_by_id(stock.product_id)
            alerts.append({
                'product': product,
                'stock': stock,
                'days_to_expiration': stock.days_to_expiration,
                'alert_level': 'critical' if stock.days_to_expiration <= 7 else 'warning'
            })
        
        return alerts
    
    def get_stock_movements(self, product_id: Optional[int] = None,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None) -> List[StockMovement]:
        """
        CASO DE USO: Obtener historial de movimientos de stock
        """
        if product_id:
            movements = self._stock_repository.find_movements_by_product_id(product_id)
        else:
            movements = []
        
        if start_date and end_date:
            date_movements = self._stock_repository.find_movements_by_date_range(start_date, end_date)
            if product_id:
                movements = [m for m in movements if start_date <= m.created_at.date() <= end_date]
            else:
                movements = date_movements
        
        return movements