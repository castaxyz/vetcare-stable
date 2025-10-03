"""
EXPLICACIÓN: Service que maneja toda la lógica de autenticación y autorización.
Coordina validaciones de credenciales, manejo de sesiones y seguridad.
"""

from typing import Optional
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from domain.entities.user import User, UserRole
from domain.value_objects.email import Email
from interfaces.repositories.user_repository import UserRepository

class AuthService:
    """
    Servicio de autenticación y autorización.
    Maneja login, logout, registro y validaciones de seguridad.
    """
    
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository
        self._max_failed_attempts = 5
        self._lockout_duration_minutes = 15
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        CASO DE USO: Autenticar usuario
        
        Args:
            username: Nombre de usuario o email
            password: Contraseña en texto plano
            
        Returns:
            User si las credenciales son válidas, None si no
            
        Raises:
            ValueError: Si la cuenta está bloqueada
        """
        # Buscar usuario por username o email
        user = self._user_repository.find_by_username(username)
        if not user:
            user = self._user_repository.find_by_email(username)
        
        if not user:
            return None
        
        # Verificar si la cuenta está bloqueada
        if user.is_locked:
            raise ValueError(f"Account is locked until {user.locked_until}")
        
        # Verificar si está activo
        if not user.is_active:
            raise ValueError("Account is inactive")
        
        # Verificar contraseña
        if not check_password_hash(user.password_hash, password):
            self._handle_failed_login(user)
            return None
        
        # Login exitoso - limpiar intentos fallidos
        self._handle_successful_login(user)
        return user
    
    def register_user(self, user_data: dict, created_by_admin: bool = False) -> User:
        """
        CASO DE USO: Registrar nuevo usuario
        
        Args:
            user_data: Datos del usuario a crear
            created_by_admin: Si fue creado por un admin (permite roles especiales)
            
        Returns:
            User creado
            
        Raises:
            ValueError: Si los datos son inválidos o ya existe el usuario
        """
        # Validar datos requeridos
        self._validate_user_registration_data(user_data)
        
        # Verificar que no exista el username
        if self._user_repository.exists_username(user_data['username']):
            raise ValueError("Username already exists")
        
        # Verificar que no exista el email
        if self._user_repository.exists_email(user_data['email']):
            raise ValueError("Email already exists")
        
        # Validar email
        email = Email(user_data['email'])
        
        # Determinar rol (solo admin puede crear otros roles)
        role = UserRole.RECEPTIONIST  # Rol por defecto
        if created_by_admin and user_data.get('role'):
            try:
                role = UserRole(user_data['role'])
            except ValueError:
                raise ValueError("Invalid role specified")
        
        # Crear entidad usuario
        user = User(
            id=None,
            username=user_data['username'],
            email=email.value,
            password_hash=generate_password_hash(user_data['password']),
            role=role,
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Guardar en repositorio
        return self._user_repository.save(user)
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        CASO DE USO: Cambiar contraseña de usuario
        """
        user = self._user_repository.find_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verificar contraseña actual
        if not check_password_hash(user.password_hash, current_password):
            raise ValueError("Current password is incorrect")
        
        # Validar nueva contraseña
        self._validate_password(new_password)
        
        # Actualizar contraseña
        user.password_hash = generate_password_hash(new_password)
        self._user_repository.update(user)
        
        return True
    
    def reset_password(self, username_or_email: str, new_password: str, admin_user_id: int) -> bool:
        """
        CASO DE USO: Reset de contraseña por admin
        """
        # Verificar que quien hace el reset es admin
        admin_user = self._user_repository.find_by_id(admin_user_id)
        if not admin_user or admin_user.role != UserRole.ADMIN:
            raise ValueError("Only admins can reset passwords")
        
        # Buscar usuario a resetear
        user = self._user_repository.find_by_username(username_or_email)
        if not user:
            user = self._user_repository.find_by_email(username_or_email)
        
        if not user:
            raise ValueError("User not found")
        
        # Validar nueva contraseña
        self._validate_password(new_password)
        
        # Actualizar contraseña y desbloquear cuenta
        user.password_hash = generate_password_hash(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None
        self._user_repository.update(user)
        
        return True
    
    def _handle_failed_login(self, user: User):
        """Maneja un intento de login fallido"""
        user.failed_login_attempts += 1
        
        # Bloquear cuenta si supera el máximo de intentos
        if user.failed_login_attempts >= self._max_failed_attempts:
            user.locked_until = datetime.utcnow() + timedelta(
                minutes=self._lockout_duration_minutes
            )
        
        self._user_repository.update(user)
    
    def _handle_successful_login(self, user: User):
        """Maneja un login exitoso"""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        self._user_repository.update(user)
    
    def _validate_user_registration_data(self, user_data: dict):
        """Valida los datos de registro de usuario"""
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        
        for field in required_fields:
            if not user_data.get(field):
                raise ValueError(f"{field} is required")
        
        # Validar longitud de username
        if len(user_data['username']) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        # Validar contraseña
        self._validate_password(user_data['password'])
    
    def _validate_password(self, password: str):
        """Valida que la contraseña cumpla los requisitos mínimos"""
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")