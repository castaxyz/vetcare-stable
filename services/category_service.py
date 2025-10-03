"""
EXPLICACIÓN: Service que maneja la lógica de negocio relacionada con categorías.
Coordina las operaciones CRUD y validaciones de categorías de productos.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities.category import Category
from interfaces.repositories.category_repository import CategoryRepository

class CategoryService:
    """
    Servicio para gestión de categorías.
    Maneja casos de uso relacionados con categorías de productos.
    """
    
    def __init__(self, category_repository: CategoryRepository):
        self._category_repository = category_repository
    
    def create_category(self, category_data: Dict[str, Any]) -> Category:
        """
        CASO DE USO: Crear nueva categoría
        
        Args:
            category_data: Diccionario con datos de la categoría
            
        Returns:
            Category creada
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        # Validar datos requeridos
        self._validate_category_data(category_data)
        
        # Verificar que el nombre sea único
        existing_category = self._category_repository.find_by_name(category_data['name'])
        if existing_category:
            raise ValueError("A category with this name already exists")
        
        # Verificar que la categoría padre existe si se proporciona
        if category_data.get('parent_id'):
            parent_category = self._category_repository.find_by_id(category_data['parent_id'])
            if not parent_category:
                raise ValueError("Parent category not found")
            if not parent_category.is_active:
                raise ValueError("Cannot create subcategory under inactive parent")
        
        # Crear la categoría
        category = Category(
            id=None,
            name=category_data['name'],
            description=category_data.get('description'),
            parent_id=category_data.get('parent_id'),
            is_active=category_data.get('is_active', True),
            created_at=datetime.now()
        )
        
        return self._category_repository.save(category)
    
    def update_category(self, category_id: int, category_data: Dict[str, Any]) -> Category:
        """
        CASO DE USO: Actualizar categoría existente
        
        Args:
            category_id: ID de la categoría
            category_data: Datos actualizados de la categoría
            
        Returns:
            Category actualizada
        """
        category = self._category_repository.find_by_id(category_id)
        if not category:
            raise ValueError("Category not found")
        
        # Verificar nombre único si se está cambiando
        if 'name' in category_data and category_data['name'] != category.name:
            existing_category = self._category_repository.find_by_name(category_data['name'])
            if existing_category and existing_category.id != category_id:
                raise ValueError("A category with this name already exists")
        
        # Verificar categoría padre si se está cambiando
        if 'parent_id' in category_data and category_data['parent_id'] != category.parent_id:
            if category_data['parent_id']:
                # Evitar ciclos en la jerarquía
                if category_data['parent_id'] == category_id:
                    raise ValueError("Category cannot be its own parent")
                
                parent_category = self._category_repository.find_by_id(category_data['parent_id'])
                if not parent_category:
                    raise ValueError("Parent category not found")
                if not parent_category.is_active:
                    raise ValueError("Cannot assign inactive parent category")
                
                # Verificar que no se cree un ciclo
                if self._would_create_cycle(category_id, category_data['parent_id']):
                    raise ValueError("This parent assignment would create a circular reference")
        
        # Actualizar campos
        for field, value in category_data.items():
            if hasattr(category, field) and field != 'id':
                setattr(category, field, value)
        
        category.updated_at = datetime.now()
        return self._category_repository.update(category)
    
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """
        CASO DE USO: Obtener categoría por ID
        """
        return self._category_repository.find_by_id(category_id)
    
    def get_all_categories(self) -> List[Category]:
        """
        CASO DE USO: Obtener todas las categorías
        """
        return self._category_repository.find_all()
    
    def get_active_categories(self) -> List[Category]:
        """
        CASO DE USO: Obtener categorías activas
        """
        return self._category_repository.find_active_categories()
    
    def get_root_categories(self) -> List[Category]:
        """
        CASO DE USO: Obtener categorías raíz (sin padre)
        """
        return self._category_repository.find_root_categories()
    
    def get_subcategories(self, parent_id: int) -> List[Category]:
        """
        CASO DE USO: Obtener subcategorías de una categoría padre
        """
        return self._category_repository.find_by_parent_id(parent_id)
    
    def get_category_hierarchy(self) -> List[Dict[str, Any]]:
        """
        CASO DE USO: Obtener jerarquía completa de categorías
        
        Returns:
            Lista de categorías con sus subcategorías anidadas
        """
        root_categories = self.get_root_categories()
        hierarchy = []
        
        for root_category in root_categories:
            category_tree = self._build_category_tree(root_category)
            hierarchy.append(category_tree)
        
        return hierarchy
    
    def deactivate_category(self, category_id: int) -> Category:
        """
        CASO DE USO: Desactivar categoría
        
        Nota: También desactiva todas las subcategorías
        """
        category = self._category_repository.find_by_id(category_id)
        if not category:
            raise ValueError("Category not found")
        
        # Verificar si tiene productos asociados
        if self._category_repository.has_products(category_id):
            raise ValueError("Cannot deactivate category with associated products")
        
        category.deactivate()
        updated_category = self._category_repository.update(category)
        
        # Desactivar subcategorías recursivamente
        subcategories = self.get_subcategories(category_id)
        for subcategory in subcategories:
            self.deactivate_category(subcategory.id)
        
        return updated_category
    
    def activate_category(self, category_id: int) -> Category:
        """
        CASO DE USO: Activar categoría
        """
        category = self._category_repository.find_by_id(category_id)
        if not category:
            raise ValueError("Category not found")
        
        # Si tiene padre, verificar que el padre esté activo
        if category.parent_id:
            parent_category = self._category_repository.find_by_id(category.parent_id)
            if not parent_category or not parent_category.is_active:
                raise ValueError("Cannot activate category with inactive parent")
        
        category.activate()
        return self._category_repository.update(category)
    
    def delete_category(self, category_id: int) -> bool:
        """
        CASO DE USO: Eliminar categoría
        
        Solo permite eliminar si no tiene productos ni subcategorías
        """
        category = self._category_repository.find_by_id(category_id)
        if not category:
            raise ValueError("Category not found")
        
        # Verificar si tiene productos asociados
        if self._category_repository.has_products(category_id):
            raise ValueError("Cannot delete category with associated products")
        
        # Verificar si tiene subcategorías
        if self._category_repository.has_subcategories(category_id):
            raise ValueError("Cannot delete category with subcategories")
        
        return self._category_repository.delete(category_id)
    
    def _build_category_tree(self, category: Category) -> Dict[str, Any]:
        """Construye el árbol de categorías recursivamente"""
        subcategories = self.get_subcategories(category.id)
        
        category_tree = {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'is_active': category.is_active,
            'parent_id': category.parent_id,
            'subcategories': []
        }
        
        for subcategory in subcategories:
            subcategory_tree = self._build_category_tree(subcategory)
            category_tree['subcategories'].append(subcategory_tree)
        
        return category_tree
    
    def _would_create_cycle(self, category_id: int, proposed_parent_id: int) -> bool:
        """Verifica si asignar un padre crearía un ciclo en la jerarquía"""
        current_id = proposed_parent_id
        
        while current_id is not None:
            if current_id == category_id:
                return True
            
            parent_category = self._category_repository.find_by_id(current_id)
            if not parent_category:
                break
            
            current_id = parent_category.parent_id
        
        return False
    
    def _validate_category_data(self, category_data: Dict[str, Any]) -> None:
        """Valida los datos de la categoría"""
        required_fields = ['name']
        
        for field in required_fields:
            if field not in category_data or not category_data[field]:
                raise ValueError(f"Field '{field}' is required")
        
        if len(category_data['name'].strip()) < 2:
            raise ValueError("Category name must be at least 2 characters long")