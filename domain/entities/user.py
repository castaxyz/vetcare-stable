"""
EXPLICACIÓN: Esta es una entidad de dominio que representa un Usuario del sistema.
Contiene SOLO lógica de negocio, sin dependencias de framework.
Principio SOLID: Single Responsibility - solo se encarga de la lógica de Usuario.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class UserRole(Enum):
    """Roles disponibles en el sistema veterinario"""
    ADMIN = "admin"
    VETERINARIAN = "veterinarian"
    RECEPTIONIST = "receptionist"
    ASSISTANT = "assistant"

@dataclass
class User:
    """
    Entidad Usuario del dominio.
    Representa un usuario del sistema veterinario con sus atributos y comportamientos.
    """
    id: Optional[int]
    username: str
    email: str
    password_hash: str
    role: UserRole
    first_name: str
    last_name: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de negocio al crear la entidad"""
        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if not self.first_name or not self.last_name:
            raise ValueError("First name and last name are required")
    
    @property
    def full_name(self) -> str:
        """Retorna el nombre completo del usuario"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_locked(self) -> bool:
        """Verifica si la cuenta está bloqueada"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    def can_perform_action(self, required_role: UserRole) -> bool:
        """Verifica si el usuario puede realizar una acción según su rol"""
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.VETERINARIAN: 3,
            UserRole.RECEPTIONIST: 2,
            UserRole.ASSISTANT: 1
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)