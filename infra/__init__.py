"""
EXPLICACIÓN: Archivo de inicialización de la capa de infraestructura.
Proporciona funciones convenientes para inicializar toda la infraestructura.
"""

from infra.database import initialize_database, create_tables, drop_tables
from infra.container import container, get_container

def initialize_infrastructure(config_name: str = 'development', create_db_tables: bool = True):
    """
    Inicializa toda la infraestructura de la aplicación.
    
    Args:
        config_name: Nombre de la configuración a usar
        create_db_tables: Si debe crear las tablas de BD
        
    Esta función debe ser llamada al inicio de la aplicación.
    """
    # 1. Inicializar base de datos
    initialize_database(config_name)
    
    # 2. Crear tablas si es necesario (útil para desarrollo)
    if create_db_tables:
        create_tables()
    
    # 3. Inicializar container de dependencias
    container.initialize()
    
    print(f"✅ Infrastructure initialized with config: {config_name}")
    print(f"📊 Container status: {container.health_check()}")

def cleanup_infrastructure():
    """
    Limpia la infraestructura. Útil para testing.
    """
    # En implementaciones futuras se podrían cerrar conexiones, etc.
    pass

__all__ = [
    'initialize_infrastructure',
    'cleanup_infrastructure', 
    'get_container',
    'container'
]