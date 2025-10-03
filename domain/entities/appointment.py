"""
EXPLICACIÓN: Entidad que representa una cita veterinaria.
Maneja la lógica de negocio de las citas médicas.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

class AppointmentStatus(Enum):
    """Estados posibles de una cita"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed" 
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class AppointmentType(Enum):
    """Tipos de citas veterinarias"""
    CONSULTATION = "consultation"
    VACCINATION = "vaccination"
    SURGERY = "surgery"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"
    GROOMING = "grooming"

@dataclass
class Appointment:
    """
    Entidad Appointment del dominio.
    Representa una cita en la clínica veterinaria.
    """
    id: Optional[int]
    pet_id: int
    veterinarian_id: Optional[int]
    appointment_date: datetime
    duration_minutes: int
    appointment_type: AppointmentType
    status: AppointmentStatus
    reason: Optional[str]
    notes: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    
    def __post_init__(self):
        """Validaciones de negocio"""

        """
        if not self.pet_id:
            raise ValueError("Pet ID is required")
        
        if self.duration_minutes <= 0 or self.duration_minutes > 480:  # Max 8 horas
            raise ValueError("Duration must be between 1 and 480 minutes")
        
        if self.appointment_date < datetime.now():
            raise ValueError("Cannot schedule appointments in the past")
        """
        if self.end_time is None:
            end_datetime = self.appointment_date + timedelta(minutes=self.duration_minutes)
            object.__setattr__(self, 'end_time', end_datetime)
        
            # COMENTAR esta validación para permitir cargar citas existentes
            # Solo validar fechas pasadas al CREAR nuevas citas, no al cargar existentes
            # if self.appointment_date.replace(tzinfo=None) < datetime.now():
            #     raise ValueError("Cannot schedule appointments in the past")
            
        if self.duration_minutes <= 0:
            raise ValueError("Duration must be positive")
        
    @property
    def end_time(self) -> datetime:
        """Calcula la hora de finalización de la cita"""
        return self.appointment_date + timedelta(minutes=self.duration_minutes)
    
    @property
    def is_upcoming(self) -> bool:
        """Verifica si la cita es próxima (dentro de las próximas 24 horas)"""
        now = datetime.now()
        return now <= self.appointment_date <= now + timedelta(hours=24)
    
    # En domain/entities/appointment.py
    @property
    def can_be_modified(self) -> bool:
        """Determina si la cita puede ser modificada"""
        return self.status in [
            AppointmentStatus.SCHEDULED, 
            AppointmentStatus.CONFIRMED, 
            AppointmentStatus.IN_PROGRESS  # AGREGAR ESTO
        ]


    def mark_as_completed(self, notes: Optional[str] = None):
        """Marca la cita como completada"""
        # CAMBIAR la validación:
        if self.status != AppointmentStatus.IN_PROGRESS:
            raise ValueError("Only appointments in progress can be completed")
        
        self.status = AppointmentStatus.COMPLETED
        if notes:
            # Si tienes campo completion_notes, usarlo; si no, usar notes
            if hasattr(self, 'completion_notes'):
                self.completion_notes = notes
            else:
                self.notes = notes
        self.updated_at = datetime.now()
    
    def cancel(self, reason: Optional[str] = None):
        """Cancela la cita"""
        if not self.can_be_modified:
            raise ValueError("Cannot cancel this appointment")
        
        self.status = AppointmentStatus.CANCELLED
        if reason:
            self.notes = f"Cancelled: {reason}"
        self.updated_at = datetime.now()