"""
EXPLICACIÓN: Interfaz para las operaciones del repositorio de citas.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, date
from domain.entities.appointment import Appointment, AppointmentStatus

class AppointmentRepository(ABC):
    """Interfaz para el repositorio de citas"""
    
    @abstractmethod
    def save(self, appointment: Appointment) -> Appointment:
        """Guarda una cita"""
        pass
    
    @abstractmethod
    def find_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """Busca cita por ID"""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Appointment]:
        """Retorna todas las citas"""
        pass
    
    @abstractmethod
    def find_by_pet_id(self, pet_id: int) -> List[Appointment]:
        """Busca citas de una mascota específica"""
        pass
    
    @abstractmethod
    def find_by_veterinarian_id(self, veterinarian_id: int) -> List[Appointment]:
        """Busca citas de un veterinario específico"""
        pass
    
    @abstractmethod
    def find_by_date(self, appointment_date: date) -> List[Appointment]:
        """Busca citas de una fecha específica"""
        pass
    
    @abstractmethod
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Appointment]:
        """Busca citas en un rango de fechas"""
        pass
    
    @abstractmethod
    def find_by_status(self, status: AppointmentStatus) -> List[Appointment]:
        """Busca citas por estado"""
        pass
    
    @abstractmethod
    def update(self, appointment: Appointment) -> Appointment:
        """Actualiza una cita"""
        pass
    
    @abstractmethod
    def delete(self, appointment_id: int) -> bool:
        """Elimina una cita"""
        pass
    
    @abstractmethod
    def find_upcoming_appointments(self, hours: int = 24) -> List[Appointment]:
        """Busca citas próximas"""
        pass
    
    @abstractmethod
    def check_availability(self, start_time: datetime, end_time: datetime, veterinarian_id: int) -> bool:
        """Verifica disponibilidad de horario"""
        pass