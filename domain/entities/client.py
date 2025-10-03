"""
EXPLICACIÓN: Entidad que representa un cliente (propietario de mascotas).
Contiene las reglas de negocio específicas de un cliente.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Client:
    """
    Entidad Cliente del dominio.
    Representa a un propietario de mascotas en la clínica veterinaria.
    """
    id: Optional[int]
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    identification_number: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de negocio"""
        if not self.first_name or not self.last_name:
            raise ValueError("First name and last name are required")
        
        if len(self.first_name) < 2 or len(self.last_name) < 2:
            raise ValueError("Names must be at least 2 characters long")
    
    @property
    def full_name(self) -> str:
        """Retorna el nombre completo del cliente"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_contact(self) -> str:
        """Retorna el contacto preferido (email o teléfono)"""
        return self.email if self.email else (self.phone if self.phone else "No contact")
    
    def has_complete_contact_info(self) -> bool:
        """Verifica si el cliente tiene información de contacto completa"""
        return bool(self.email or self.phone)