"""
EXPLICACIÓN: Módulo de inicialización de base de datos.
Maneja la creación de tablas y configuración inicial de la base de datos.
"""

from infra.database.connection import (
    get_engine,
    init_database,
    create_tables as create_db_tables,
    drop_tables as drop_db_tables,
    get_db_session
)
from config.settings import config
import os

def initialize_database(config_name: str = 'development'):
    """
    Inicializa la configuración de base de datos.

    Args:
        config_name: Nombre de la configuración ('development', 'production', 'testing')
    """
    # Configurar el engine de SQLAlchemy
    engine = get_engine()
    print(f"📊 Database engine initialized: {engine.url}")

    return engine

def create_tables():
    """
    Crea todas las tablas definidas en los modelos.
    """
    try:
        create_db_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise

def drop_tables():
    """
    Elimina todas las tablas.
    ¡CUIDADO! Solo usar en desarrollo.
    """
    try:
        drop_db_tables()
        print("⚠️ All database tables dropped")
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        raise

def reset_database():
    """
    Reinicia la base de datos (elimina y crea todas las tablas).
    ¡CUIDADO! Solo usar en desarrollo.
    """
    print("🔄 Resetting database...")
    drop_tables()
    create_tables()
    print("✅ Database reset completed")

def check_database_health():
    """
    Verifica el estado de la base de datos.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Intentar una consulta simple
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return True
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Intentar una consulta simple
            result = conn.execute("SELECT 1")
            result.fetchone()
        return True
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False