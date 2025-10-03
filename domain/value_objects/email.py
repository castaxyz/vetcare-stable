"""
EXPLICACIÓN: Value Object para representar un email.
Los Value Objects son inmutables y se comparan por valor, no por identidad.
Encapsulan validaciones y comportamientos específicos del valor.
"""

import re
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)  # frozen=True hace el objeto inmutable
class Email:
    """
    Value Object que representa un email válido.
    Garantiza que el email tenga un formato correcto.
    """
    value: str
    
    def __post_init__(self):
        """Valida el formato del email al crear el objeto"""
        if not self.value:
            raise ValueError("Email cannot be empty")
        
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
    
    def _is_valid_email(self, email: str) -> bool:
        """Valida el formato del email usando regex"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    @property
    def domain(self) -> str:
        """Extrae el dominio del email"""
        return self.value.split('@')[1]
    
    @property
    def local_part(self) -> str:
        """Extrae la parte local del email (antes del @)"""
        return self.value.split('@')[0]
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def create_optional(cls, email_str: Optional[str]) -> Optional['Email']:
        """Crea un Email opcional (puede ser None)"""
        if not email_str:
            return None
        return cls(email_str)