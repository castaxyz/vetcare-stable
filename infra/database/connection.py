"""
EXPLICACIÓN: Módulo de conexión a la base de datos.
Maneja la configuración y conexión con SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import config
import os

# Variable global para el engine
_engine = None
_session_factory = None

def get_engine():
    """
    Obtiene la instancia del engine de SQLAlchemy.
    Implementa patrón Singleton para reutilizar la conexión.
    Usa valores por defecto si la configuración no define las propiedades esperadas.
    """
    global _engine
    if _engine is None:
        # Obtener configuración actual
        config_name = os.environ.get('FLASK_CONFIG', 'development')
        cfg = config.get(config_name) if hasattr(config, 'get') else config[config_name]

        # Valor por defecto para la URL de la base de datos
        default_db_url = os.environ.get('DATABASE_URL', 'sqlite:///./dev.db')

        # Determinar database_url desde la configuración o usar el valor por defecto
        if cfg is None:
            database_url = default_db_url
        else:
            # Soportar tanto objetos con atributos como dicts
            if isinstance(cfg, dict):
                database_url = cfg.get('SQLALCHEMY_DATABASE_URI', os.environ.get('DATABASE_URL', default_db_url))
                echo_cfg = cfg.get('SQLALCHEMY_ECHO', None)
            else:
                database_url = getattr(cfg, 'SQLALCHEMY_DATABASE_URI', os.environ.get('DATABASE_URL', default_db_url))
                echo_cfg = getattr(cfg, 'SQLALCHEMY_ECHO', None)

        # Determinar si mostrar SQL queries:
        # Preferir la configuración, si no existe, usar la variable de entorno (True/False) y por último False.
        if 'echo_cfg' in locals() and echo_cfg is not None:
            if isinstance(echo_cfg, str):
                echo_sql = echo_cfg.lower() == 'true'
            else:
                echo_sql = bool(echo_cfg)
        else:
            echo_sql = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'

        # Crear engine con configuración optimizada
        _engine = create_engine(
            database_url,
            echo=echo_sql,
            pool_pre_ping=True,  # Verificar conexiones antes de usar
            pool_recycle=3600,   # Reciclar conexiones cada hora
        )

    return _engine

def get_session_factory():
    """
    Obtiene la factory de sesiones de SQLAlchemy.
    """
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine)

    return _session_factory

def create_tables():
    """
    Crea todas las tablas definidas en los modelos.
    Útil para desarrollo y testing.
    """
    from infra.database.models import Base
    engine = get_engine()
    Base.metadata.create_all(engine)

def drop_tables():
    """
    Elimina todas las tablas.
    ¡CUIDADO! Solo usar en desarrollo.
    """
    from infra.database.models import Base
    engine = get_engine()
    Base.metadata.drop_all(engine)

def get_db_session():
    """
    Obtiene una nueva sesión de base de datos.
    Recuerda cerrar la sesión después de usar.
    """
    Session = get_session_factory()
    return Session()

def init_database():
    """
    Inicializa la base de datos creando las tablas si no existen.
    """
    try:
        create_tables()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    return Session()

def init_database():
    """
    Inicializa la base de datos creando las tablas si no existen.
    """
    try:
        create_tables()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False