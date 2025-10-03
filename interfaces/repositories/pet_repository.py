"""
EXPLICACIÓN: Interfaz para las operaciones del repositorio de mascotas.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.pet import Pet

class PetRepository(ABC):
    """Interfaz para el repositorio de mascotas"""
    
    @abstractmethod
    def save(self, pet: Pet) -> Pet:
        """Guarda una mascota"""
        pass
    
    @abstractmethod
    def find_by_id(self, pet_id: int) -> Optional[Pet]:
        """Busca mascota por ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Pet]:
        """Retorna todas las mascotas"""
        pass
    
    @abstractmethod
    def find_by_client_id(self, client_id: int) -> List[Pet]:
        """Busca mascotas de un cliente específico"""
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> List[Pet]:
        """Busca mascotas por nombre"""
        pass
    
    @abstractmethod
    def find_by_microchip(self, microchip: str) -> Optional[Pet]:
        """Busca mascota por microchip"""
        pass
    
    @abstractmethod
    def update(self, pet: Pet) -> Pet:
        """Actualiza una mascota"""
        pass
    
    @abstractmethod
    def delete(self, pet_id: int) -> bool:
        """Elimina una mascota"""
        pass
    
    @abstractmethod
    def find_active_pets(self) -> List[Pet]:
        """Retorna solo mascotas activas"""
        pass