"""
EXPLICACIÓN: Interfaz que define las operaciones del repositorio de clientes.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.client import Client

class ClientRepository(ABC):
    """Interfaz para el repositorio de clientes"""
    
    @abstractmethod
    def save(self, client: Client) -> Client:
        """Guarda un cliente"""
        pass
    
    @abstractmethod
    def find_by_id(self, client_id: int) -> Optional[Client]:
        """Busca cliente por ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Client]:
        """Retorna todos los clientes"""
        pass
    
    @abstractmethod
    def find_by_name(self, first_name: str, last_name: str) -> List[Client]:
        """Busca clientes por nombre"""
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Client]:
        """Busca cliente por email"""
        pass
    
    @abstractmethod
    def find_by_identification(self, identification: str) -> Optional[Client]:
        """Busca cliente por número de identificación"""
        pass
    
    @abstractmethod
    def update(self, client: Client) -> Client:
        """Actualiza un cliente"""
        pass
    
    @abstractmethod
    def delete(self, client_id: int) -> bool:
        """Elimina un cliente"""
        pass
    
    @abstractmethod
    def search(self, query: str) -> List[Client]:
        """Busca clientes por término de búsqueda"""
        pass