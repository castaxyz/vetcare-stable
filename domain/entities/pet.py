"""
EXPLICACIÓN: Entidad que representa una mascota.
Contiene la lógica de negocio relacionada con las mascotas.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from enum import Enum

class PetGender(Enum):
    """Géneros disponibles para mascotas"""
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class PetSpecies(Enum):
    """Especies principales en una clínica veterinaria"""
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    RABBIT = "rabbit"
    HAMSTER = "hamster"
    OTHER = "other"

@dataclass
class Pet:
    """
    Entidad Pet del dominio.
    Representa una mascota en la clínica veterinaria.
    """
    id: Optional[int]
    name: str
    species: PetSpecies
    breed: Optional[str]
    birth_date: Optional[date]
    gender: PetGender
    color: Optional[str]
    weight: Optional[float]
    microchip_number: Optional[str]
    client_id: int
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones de negocio"""
        if not self.name or len(self.name) < 1:
            raise ValueError("Pet name is required")
        
        if self.weight is not None and self.weight <= 0:
            raise ValueError("Weight must be positive")
        
        if not self.client_id:
            raise ValueError("Client ID is required")
    
    @property
    def age_in_years(self) -> Optional[int]:
        """Calcula la edad de la mascota en años"""
        if not self.birth_date:
            return None
        
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    @property
    def display_info(self) -> str:
        """Información básica de la mascota para mostrar"""
        age_info = f", {self.age_in_years} años" if self.age_in_years else ""
        return f"{self.name} ({self.species.value.title()}{age_info})"
    
    def needs_vaccination_reminder(self) -> bool:
        """Determina si necesita recordatorio de vacunación (lógica simplificada)"""
        if not self.birth_date:
            return False
        return self.age_in_years and self.age_in_years >= 1