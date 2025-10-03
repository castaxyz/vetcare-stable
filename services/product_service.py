"""
EXPLICACIÓN: Service que maneja la lógica de negocio relacionada con productos.
Coordina las operaciones CRUD y validaciones de productos del inventario.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities.product import Product, ProductStatus, ProductType
from interfaces.repositories.product_repository import ProductRepository
from interfaces.repositories.category_repository import CategoryRepository

class ProductService:
    """
    Servicio para gestión de productos.
    Maneja casos de uso relacionados con productos del inventario.
    """
    
    def __init__(self, 
                 product_repository: ProductRepository,
                 category_repository: CategoryRepository):
        self._product_repository = product_repository
        self._category_repository = category_repository
    
    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """
        CASO DE USO: Crear nuevo producto
        
        Args:
            product_data: Diccionario con datos del producto
            
        Returns:
            Product creado
            
        Raises:
            ValueError: Si los datos son inválidos o ya existe el SKU
        """
        # Validar datos requeridos
        self._validate_product_data(product_data)
        
        # Verificar que el SKU sea único
        existing_product = self._product_repository.find_by_sku(product_data['sku'])
        if existing_product:
            raise ValueError("A product with this SKU already exists")
        
        # Verificar que la categoría existe si se proporciona
        if product_data.get('category_id'):
            category = self._category_repository.find_by_id(product_data['category_id'])
            if not category:
                raise ValueError("Category not found")
            if not category.is_active:
                raise ValueError("Cannot assign product to inactive category")
        
        # Crear el producto
        product = Product(
            id=None,
            name=product_data['name'],
            description=product_data.get('description'),
            sku=product_data['sku'],
            category_id=product_data.get('category_id'),
            product_type=ProductType(product_data['product_type']),
            unit_price=product_data['unit_price'],
            cost_price=product_data['cost_price'],
            status=ProductStatus(product_data.get('status', ProductStatus.ACTIVE.value)),
            minimum_stock=product_data.get('minimum_stock', 0),
            maximum_stock=product_data.get('maximum_stock'),
            reorder_point=product_data.get('reorder_point', 0),
            supplier=product_data.get('supplier'),
            expiration_tracking=product_data.get('expiration_tracking', False),
            created_at=datetime.now()
        )
        
        return self._product_repository.save(product)
    
    def update_product(self, product_id: int, product_data: Dict[str, Any]) -> Product:
        """
        CASO DE USO: Actualizar producto existente
        
        Args:
            product_id: ID del producto
            product_data: Datos actualizados del producto
            
        Returns:
            Product actualizado
        """
        product = self._product_repository.find_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        # Verificar SKU único si se está cambiando
        if 'sku' in product_data and product_data['sku'] != product.sku:
            existing_product = self._product_repository.find_by_sku(product_data['sku'])
            if existing_product and existing_product.id != product_id:
                raise ValueError("A product with this SKU already exists")
        
        # Verificar categoría si se está cambiando
        if 'category_id' in product_data and product_data['category_id'] != product.category_id:
            if product_data['category_id']:
                category = self._category_repository.find_by_id(product_data['category_id'])
                if not category:
                    raise ValueError("Category not found")
                if not category.is_active:
                    raise ValueError("Cannot assign product to inactive category")
        
        # Actualizar campos
        for field, value in product_data.items():
            if hasattr(product, field) and field != 'id':
                if field == 'product_type':
                    setattr(product, field, ProductType(value))
                elif field == 'status':
                    setattr(product, field, ProductStatus(value))
                else:
                    setattr(product, field, value)
        
        product.updated_at = datetime.now()
        return self._product_repository.update(product)
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        CASO DE USO: Obtener producto por ID
        """
        return self._product_repository.find_by_id(product_id)
    
    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """
        CASO DE USO: Obtener producto por SKU
        """
        return self._product_repository.find_by_sku(sku)
    
    def search_products(self, search_term: str) -> List[Product]:
        """
        CASO DE USO: Buscar productos por nombre
        """
        return self._product_repository.find_by_name(search_term)
    
    def get_products_by_category(self, category_id: int) -> List[Product]:
        """
        CASO DE USO: Obtener productos por categoría
        """
        return self._product_repository.find_by_category_id(category_id)
    
    def get_products_by_type(self, product_type: ProductType) -> List[Product]:
        """
        CASO DE USO: Obtener productos por tipo
        """
        return self._product_repository.find_by_type(product_type)
    
    def get_active_products(self) -> List[Product]:
        """
        CASO DE USO: Obtener productos activos
        """
        return self._product_repository.find_active_products()

    def get_all_products(self) -> List[Product]:
        """
        CASO DE USO: Obtener todos los productos
        """
        return self._product_repository.find_all()

    def get_low_stock_products(self) -> List[Product]:
        """
        CASO DE USO: Obtener productos con stock bajo
        """
        return self._product_repository.find_low_stock_products()

    def get_products_by_status(self, status: ProductStatus) -> List[Product]:
        """
        CASO DE USO: Obtener productos por estado

        Args:
            status: Estado de los productos a buscar

        Returns:
            Lista de productos con el estado especificado
        """
        return self._product_repository.find_by_status(status)
    
    def deactivate_product(self, product_id: int) -> Product:
        """
        CASO DE USO: Desactivar producto
        """
        product = self._product_repository.find_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        product.deactivate()
        product.updated_at = datetime.now()
        return self._product_repository.update(product)
    
    def activate_product(self, product_id: int) -> Product:
        """
        CASO DE USO: Activar producto
        """
        product = self._product_repository.find_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        product.activate()
        product.updated_at = datetime.now()
        return self._product_repository.update(product)
    
    def discontinue_product(self, product_id: int) -> Product:
        """
        CASO DE USO: Descontinuar producto
        """
        product = self._product_repository.find_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        
        product.discontinue()
        product.updated_at = datetime.now()
        return self._product_repository.update(product)
    
    def _validate_product_data(self, product_data: Dict[str, Any]) -> None:
        """Valida los datos del producto"""
        required_fields = ['name', 'sku', 'product_type', 'unit_price', 'cost_price']
        
        for field in required_fields:
            if field not in product_data or product_data[field] is None:
                raise ValueError(f"Field '{field}' is required")
        
        if len(product_data['name'].strip()) < 2:
            raise ValueError("Product name must be at least 2 characters long")
        
        if len(product_data['sku'].strip()) < 3:
            raise ValueError("SKU must be at least 3 characters long")
        
        if product_data['unit_price'] < 0:
            raise ValueError("Unit price cannot be negative")
        
        if product_data['cost_price'] < 0:
            raise ValueError("Cost price cannot be negative")
        
        if product_data.get('minimum_stock', 0) < 0:
            raise ValueError("Minimum stock cannot be negative")
        
        if product_data.get('reorder_point', 0) < 0:
            raise ValueError("Reorder point cannot be negative")
        
        max_stock = product_data.get('maximum_stock')
        min_stock = product_data.get('minimum_stock', 0)
        if max_stock is not None and max_stock < min_stock:
            raise ValueError("Maximum stock cannot be less than minimum stock")