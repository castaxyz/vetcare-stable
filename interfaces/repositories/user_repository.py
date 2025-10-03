"""
EXPLICACIÓN: Esta es una INTERFAZ (contrato) que define QUÉ operaciones 
debe implementar cualquier repositorio de usuarios.
Principio SOLID: Dependency Inversion - dependemos de abstracciones, no de concreciones.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.user import User

class UserRepository(ABC):
    """
    Interfaz que define las operaciones disponibles para el repositorio de usuarios.
    Cualquier implementación concreta debe implementar todos estos métodos.
    """
    
    @abstractmethod
    def save(self, user: User) -> User:
        """
        Guarda un usuario en el sistema de persistencia.
        Retorna el usuario guardado con su ID asignado.
        """
        pass
    
    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]:
        """
        Busca un usuario por su ID.
        Retorna None si no lo encuentra.
        """
        pass
    
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """
        Busca un usuario por su nombre de usuario.
        Retorna None si no lo encuentra.
        """
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]:
        """
        Busca un usuario por su email.
        Retorna None si no lo encuentra.
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[User]:
        """
        Retorna todos los usuarios del sistema.
        """
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """
        Actualiza un usuario existente.
        """
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """
        Elimina un usuario por su ID.
        Retorna True si fue eliminado exitosamente.
        """
        pass
    
    @abstractmethod
    def exists_username(self, username: str) -> bool:
        """
        Verifica si ya existe un usuario con ese username.
        """
        pass
    
    @abstractmethod
    def exists_email(self, email: str) -> bool:
        """
        Verifica si ya existe un usuario con ese email.
        """
        pass