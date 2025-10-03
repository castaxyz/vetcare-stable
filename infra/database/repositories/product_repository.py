"""
EXPLICACIÓN: Implementación básica SQLAlchemy del repositorio de productos.
Versión simplificada para funcionalidad básica.
"""

from typing import List, Optional
from sqlalchemy.orm import sessionmaker

from interfaces.repositories.product_repository import ProductRepository
from domain.entities.product import Product, ProductStatus, ProductType
from infra.database.models import ProductModel
from infra.database.connection import get_engine

class SQLProductRepository(ProductRepository):
    """Implementación SQLAlchemy del repositorio de productos"""
    
    def __init__(self):
        self.engine = get_engine()
        self.Session = sessionmaker(bind=self.engine)
    
    def save(self, product: Product) -> Product:
        """Guarda un producto"""
        session = self.Session()
        try:
            if product.id is None:
                product_model = self._domain_to_model(product)
                session.add(product_model)
                session.flush()
                product.id = product_model.id
                session.commit()
                return product
            else:
                product_model = session.query(ProductModel).filter_by(id=product.id).first()
                if not product_model:
                    raise ValueError("Product not found")
                self._update_model_from_domain(product_model, product)
                session.commit()
                return product
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_by_id(self, product_id: int) -> Optional[Product]:
        """Busca producto por ID"""
        session = self.Session()
        try:
            product_model = session.query(ProductModel).filter_by(id=product_id).first()
            if not product_model:
                return None
            return self._model_to_domain(product_model)
        finally:
            session.close()
    
    def find_all(self) -> List[Product]:
        """Retorna todos los productos"""
        session = self.Session()
        try:
            product_models = session.query(ProductModel).order_by(ProductModel.name).all()
            return [self._model_to_domain(model) for model in product_models]
        finally:
            session.close()
    
    def find_by_sku(self, sku: str) -> Optional[Product]:
        """Busca producto por SKU"""
        session = self.Session()
        try:
            product_model = session.query(ProductModel).filter_by(sku=sku).first()
            if not product_model:
                return None
            return self._model_to_domain(product_model)
        finally:
            session.close()
    
    def find_by_name(self, name: str) -> List[Product]:
        """Busca productos por nombre"""
        session = self.Session()
        try:
            product_models = session.query(ProductModel)\
                .filter(ProductModel.name.ilike(f'%{name}%')).all()
            return [self._model_to_domain(model) for model in product_models]
        finally:
            session.close()
    
    def find_by_category_id(self, category_id: int) -> List[Product]:
        """Busca productos por categoría"""
        session = self.Session()
        try:
            product_models = session.query(ProductModel)\
                .filter_by(category_id=category_id).all()
            return [self._model_to_domain(model) for model in product_models]
        finally:
            session.close()
    
    def find_by_type(self, product_type: ProductType) -> List[Product]:
        """Busca productos por tipo"""
        session = self.Session()
        try:
            product_models = session.query(ProductModel)\
                .filter_by(product_type=product_type).all()
            return [self._model_to_domain(model) for model in product_models]
        finally:
            session.close()
    
    def find_by_status(self, status: ProductStatus) -> List[Product]:
        """Busca productos por estado"""
        session = self.Session()
        try:
            product_models = session.query(ProductModel)\
                .filter_by(status=status.value).all()  # Usar .value para obtener el string
            return [self._model_to_domain(model) for model in product_models]
        finally:
            session.close()
    
    def find_active_products(self) -> List[Product]:
        """Busca productos activos"""
        return self.find_by_status(ProductStatus.ACTIVE)
    
    def find_by_supplier(self, supplier: str) -> List[Product]:
        """Busca productos por proveedor"""
        session = self.Session()
        try:
            product_models = session.query(ProductModel)\
                .filter(ProductModel.supplier.ilike(f'%{supplier}%')).all()
            return [self._model_to_domain(model) for model in product_models]
        finally:
            session.close()
    
    def find_low_stock_products(self) -> List[Product]:
        """Busca productos con stock bajo"""
        # Implementación básica - retorna lista vacía por ahora
        return []
    
    def update(self, product: Product) -> Product:
        """Actualiza un producto"""
        return self.save(product)
    
    def delete(self, product_id: int) -> bool:
        """Elimina un producto"""
        session = self.Session()
        try:
            product_model = session.query(ProductModel).filter_by(id=product_id).first()
            if not product_model:
                return False
            session.delete(product_model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def _domain_to_model(self, product: Product) -> ProductModel:
        """Convierte entidad de dominio a modelo SQLAlchemy"""
        return ProductModel(
            name=product.name,
            description=product.description,
            sku=product.sku,
            category_id=product.category_id,
            product_type=product.product_type,
            unit_price=product.unit_price,
            cost_price=product.cost_price,
            status=product.status,
            minimum_stock=product.minimum_stock,
            maximum_stock=product.maximum_stock,
            reorder_point=product.reorder_point,
            supplier=product.supplier,
            expiration_tracking=product.expiration_tracking,
            created_at=product.created_at,
            updated_at=product.updated_at
        )
    
    def _model_to_domain(self, model: ProductModel) -> Product:
        """Convierte modelo SQLAlchemy a entidad de dominio"""
        return Product(
            id=model.id,
            name=model.name,
            description=model.description,
            sku=model.sku,
            category_id=model.category_id,
            product_type=model.product_type,
            unit_price=model.unit_price,
            cost_price=model.cost_price,
            status=model.status,
            minimum_stock=model.minimum_stock,
            maximum_stock=model.maximum_stock,
            reorder_point=model.reorder_point,
            supplier=model.supplier,
            expiration_tracking=model.expiration_tracking,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _update_model_from_domain(self, model: ProductModel, product: Product):
        """Actualiza modelo SQLAlchemy desde entidad de dominio"""
        model.name = product.name
        model.description = product.description
        model.sku = product.sku
        model.category_id = product.category_id
        model.product_type = product.product_type
        model.unit_price = product.unit_price
        model.cost_price = product.cost_price
        model.status = product.status
        model.minimum_stock = product.minimum_stock
        model.maximum_stock = product.maximum_stock
        model.reorder_point = product.reorder_point
        model.supplier = product.supplier
        model.expiration_tracking = product.expiration_tracking
        model.updated_at = product.updated_at