"""
EXPLICACIÓN: Este archivo centraliza todas las configuraciones de la aplicación.
Principio SOLID aplicado: Single Responsibility (una sola razón para cambiar).
Permite diferentes configuraciones para desarrollo, testing y producción.
"""

import os
from datetime import timedelta

class Config:
    """Configuración base para toda la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-university'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuraciones de sesión
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Configuraciones de paginación
    ITEMS_PER_PAGE = 10

class DevelopmentConfig(Config):
    """Configuración para desarrollo local"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///vetcare_dev.db'

class ProductionConfig(Config):
    """Configuración para producción (Azure)"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///vetcare_prod.db'

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Diccionario para seleccionar configuración fácilmente
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}