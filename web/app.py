"""
EXPLICACIÓN: Factory pattern para crear la aplicación Flask.
Implementa el patrón Application Factory para facilitar testing y configuración.
Este es el "corazón" de la aplicación web.
"""

from flask import Flask, redirect, url_for, session, flash, request, render_template
from flask_migrate import Migrate
from datetime import timedelta, datetime
import os

from config.settings import config
from infra import initialize_infrastructure, get_container

# Extensiones globales
migrate = Migrate()

def create_app(config_name: str = None) -> Flask:
    """
    Factory function para crear la aplicación Flask.
    
    Args:
        config_name: Nombre de la configuración ('development', 'production', 'testing')
        
    Returns:
        Aplicación Flask configurada y lista para usar
    """
    
    # Determinar configuración
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    # Crear aplicación Flask
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Configurar sesiones
    app.permanent_session_lifetime = timedelta(hours=2)
    
    # Inicializar infraestructura
    initialize_infrastructure(config_name)
    
    # Inicializar extensiones
    migrate.init_app(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Registrar manejadores de errores
    register_error_handlers(app)
    
    # Registrar context processors
    register_context_processors(app)
    
    # Registrar middleware
    register_middleware(app)
    
    print(f"✅ Flask app created with config: {config_name}")
    
    return app

def register_blueprints(app: Flask):
    """Registra todos los blueprints de la aplicación"""

    # Blueprint de autenticación
    from web.blueprints.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Blueprint de dashboard principal
    from web.blueprints.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    # Blueprint de clientes
    from web.blueprints.clients import clients_bp
    app.register_blueprint(clients_bp, url_prefix='/clients')

    # Blueprint de mascotas
    from web.blueprints.pets import pets_bp
    app.register_blueprint(pets_bp, url_prefix='/pets')

    # Blueprint de citas
    from web.blueprints.appointments import appointments_bp
    app.register_blueprint(appointments_bp, url_prefix='/appointments')

    # Blueprint de facturación
    from web.blueprints.invoices import invoices_bp
    app.register_blueprint(invoices_bp, url_prefix='/invoices')

    # Blueprint de inventario
    from web.blueprints.inventory import inventory_bp
    app.register_blueprint(inventory_bp, url_prefix='/inventory')

    # Ruta raíz
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

def register_error_handlers(app: Flask):
    """Registra manejadores de errores personalizados"""
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

def register_context_processors(app: Flask):
    """Registra variables globales disponibles en todos los templates"""
    
    @app.context_processor
    def inject_user_info():
        """Inyecta información del usuario logueado en todos los templates"""
        user_info = {}
        
        if 'user_id' in session:
            try:
                container = get_container()
                auth_service = container.get_auth_service()
                user_repo = container.get_user_repository()
                
                user = user_repo.find_by_id(session['user_id'])
                if user:
                    user_info = {
                        'current_user': user,
                        'is_admin': user.role.value == 'admin',
                        'is_veterinarian': user.role.value in ['admin', 'veterinarian'],
                        'can_manage_users': user.role.value == 'admin'
                    }
            except Exception as e:
                print(f"Error loading user info: {e}")
                # Limpiar sesión si hay error
                session.clear()
        
        return user_info
    
    @app.context_processor
    def inject_app_info():
        """Inyecta información general de la aplicación"""
        return {
            'app_name': 'VetCare',
            'app_version': '1.0.0',
            'current_year': datetime.now().year
        }

def register_middleware(app: Flask):
    """Registra middleware personalizado"""
    
    @app.before_request
    def require_login():
        """Middleware que requiere autenticación para rutas protegidas"""
        
        # Rutas públicas que no requieren autenticación
        public_routes = [
            'auth.login',
            'auth.register', 
            'static',
            'auth.logout'  # logout debe ser accesible siempre
        ]
        
        # Permitir archivos estáticos
        if request.endpoint and (
            request.endpoint in public_routes or 
            request.endpoint.startswith('static')
        ):
            return
        
        # Verificar si el usuario está logueado
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Verificar que el usuario aún existe y está activo
        try:
            container = get_container()
            user_repo = container.get_user_repository()
            user = user_repo.find_by_id(session['user_id'])
            
            if not user or not user.is_active:
                session.clear()
                flash('Tu cuenta ha sido desactivada.', 'error')
                return redirect(url_for('auth.login'))
                
        except Exception as e:
            print(f"Error checking user status: {e}")
            session.clear()
            return redirect(url_for('auth.login'))
    
    @app.after_request
    def after_request(response):
        """Middleware ejecutado después de cada request"""
        # Headers de seguridad básicos
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        return response

# Función helper para crear la app con configuración por defecto
def create_development_app():
    """Crea app para desarrollo local"""
    return create_app('development')

def create_production_app():
    """Crea app para producción"""
    return create_app('production')

def create_testing_app():
    """Crea app para testing"""
    return create_app('testing')