"""
EXPLICACIÓN: Blueprint de autenticación que maneja login, logout y registro.
Implementa validaciones de seguridad y manejo de sesiones.
Es la puerta de entrada a la aplicación.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.exceptions import BadRequest
from datetime import datetime

from infra import get_container
from domain.entities.user import UserRole

# Crear blueprint
auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    RUTA: Página de inicio de sesión
    GET: Muestra formulario de login
    POST: Procesa credenciales de login
    """
    
    # Si ya está logueado, redirigir al dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'GET':
        return render_template('auth/login.html')
    
    # Procesar POST - intento de login
    try:
        # Obtener datos del formulario
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        # Validaciones básicas
        if not username or not password:
            flash('Por favor ingresa usuario y contraseña.', 'error')
            return render_template('auth/login.html', username=username)
        
        # Intentar autenticación
        container = get_container()
        auth_service = container.get_auth_service()
        
        user = auth_service.authenticate(username, password)
        
        if user:
            # Login exitoso - crear sesión
            session.permanent = remember_me
            session['user_id'] = user.id
            session['user_role'] = user.role.value
            session['user_name'] = user.full_name
            session['login_time'] = datetime.utcnow().isoformat()
            
            flash(f'¡Bienvenido, {user.first_name}!', 'success')
            
            # Redirigir a la página que intentaba acceder o al dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('dashboard.index'))
        else:
            flash('Credenciales incorrectas.', 'error')
            return render_template('auth/login.html', username=username)
            
    except ValueError as e:
        # Errores de validación (cuenta bloqueada, inactiva, etc.)
        flash(str(e), 'error')
        return render_template('auth/login.html', username=username)
    
    except Exception as e:
        print(f"Error en login: {e}")
        flash('Error interno. Intenta nuevamente.', 'error')
        return render_template('auth/login.html', username=username)

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    """
    RUTA: Cerrar sesión
    Limpia la sesión y redirige al login
    """
    user_name = session.get('user_name', 'Usuario')
    
    # Limpiar sesión
    session.clear()
    
    flash(f'Hasta luego, {user_name}!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    RUTA: Registro de nuevos usuarios
    Solo disponible para administradores
    """
    
    # Verificar que el usuario actual es admin
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        container = get_container()
        user_repo = container.get_user_repository()
        current_user = user_repo.find_by_id(session['user_id'])
        
        if not current_user or current_user.role != UserRole.ADMIN:
            flash('Solo los administradores pueden registrar nuevos usuarios.', 'error')
            return redirect(url_for('dashboard.index'))
    
    except Exception as e:
        flash('Error verificando permisos.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'GET':
        return render_template('auth/register.html', roles=UserRole)
    
    # Procesar POST - crear usuario
    try:
        # Obtener datos del formulario
        user_data = {
            'username': request.form.get('username', '').strip().lower(),
            'email': request.form.get('email', '').strip().lower(),
            'password': request.form.get('password', ''),
            'password_confirm': request.form.get('password_confirm', ''),
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'role': request.form.get('role', 'receptionist')
        }
        
        # Validaciones del formulario
        errors = []
        
        if not user_data['username'] or len(user_data['username']) < 3:
            errors.append('El nombre de usuario debe tener al menos 3 caracteres.')
        
        if not user_data['email'] or '@' not in user_data['email']:
            errors.append('Ingresa un email válido.')
        
        if not user_data['password'] or len(user_data['password']) < 6:
            errors.append('La contraseña debe tener al menos 6 caracteres.')
        
        if user_data['password'] != user_data['password_confirm']:
            errors.append('Las contraseñas no coinciden.')
        
        if not user_data['first_name'] or not user_data['last_name']:
            errors.append('Nombre y apellido son requeridos.')
        
        # Validar rol
        try:
            UserRole(user_data['role'])
        except ValueError:
            errors.append('Rol inválido seleccionado.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html', roles=UserRole, **user_data)
        
        # Intentar crear usuario
        auth_service = container.get_auth_service()
        
        new_user = auth_service.register_user(
            user_data=user_data,
            created_by_admin=True
        )
        
        flash(f'Usuario {new_user.username} creado exitosamente.', 'success')
        return redirect(url_for('dashboard.users'))
        
    except ValueError as e:
        flash(str(e), 'error')
        return render_template('auth/register.html', roles=UserRole, **user_data)
    
    except Exception as e:
        print(f"Error en registro: {e}")
        flash('Error creando usuario. Intenta nuevamente.', 'error')
        return render_template('auth/register.html', roles=UserRole, **user_data)

@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """
    RUTA: Perfil del usuario actual
    Permite cambiar contraseña y datos básicos
    """
    try:
        container = get_container()
        user_repo = container.get_user_repository()
        current_user = user_repo.find_by_id(session['user_id'])
        
        if not current_user:
            flash('Usuario no encontrado.', 'error')
            return redirect(url_for('auth.logout'))
        
    except Exception as e:
        flash('Error cargando perfil.', 'error')
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'GET':
        return render_template('auth/profile.html', user=current_user)
    
    # Procesar POST - actualizar perfil
    try:
        action = request.form.get('action')
        
        if action == 'change_password':
            # Cambiar contraseña
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not current_password or not new_password:
                flash('Todos los campos son requeridos.', 'error')
                return render_template('auth/profile.html', user=current_user)
            
            if new_password != confirm_password:
                flash('Las contraseñas nuevas no coinciden.', 'error')
                return render_template('auth/profile.html', user=current_user)
            
            if len(new_password) < 6:
                flash('La contraseña debe tener al menos 6 caracteres.', 'error')
                return render_template('auth/profile.html', user=current_user)
            
            # Cambiar contraseña usando el service
            auth_service = container.get_auth_service()
            auth_service.change_password(
                user_id=current_user.id,
                current_password=current_password,
                new_password=new_password
            )
            
            flash('Contraseña actualizada exitosamente.', 'success')
            
        elif action == 'update_info':
            # Actualizar información básica
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            
            if not current_user.first_name or not current_user.last_name:
                flash('Nombre y apellido son requeridos.', 'error')
                return render_template('auth/profile.html', user=current_user)
            
            # Actualizar usuario
            user_repo.update(current_user)
            
            # Actualizar nombre en sesión
            session['user_name'] = current_user.full_name
            
            flash('Información actualizada exitosamente.', 'success')
        
        return redirect(url_for('auth.profile'))
        
    except ValueError as e:
        flash(str(e), 'error')
        return render_template('auth/profile.html', user=current_user)
    
    except Exception as e:
        print(f"Error actualizando perfil: {e}")
        flash('Error actualizando perfil.', 'error')
        return render_template('auth/profile.html', user=current_user)