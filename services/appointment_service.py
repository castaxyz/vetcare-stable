"""
EXPLICACIÓN: Service que maneja la lógica de negocio de citas veterinarias.
Coordina la programación, validaciones y gestión de citas.
"""

from typing import List, Optional
from datetime import datetime, timedelta, date

from domain.entities.appointment import Appointment, AppointmentStatus, AppointmentType
from interfaces.repositories.appointment_repository import AppointmentRepository
from interfaces.repositories.pet_repository import PetRepository
from interfaces.repositories.user_repository import UserRepository

class AppointmentService:
    """
    Servicio para gestión de citas veterinarias.
    Maneja programación, validaciones y seguimiento de citas.
    """
    
    def __init__(
        self, 
        appointment_repository: AppointmentRepository,
        pet_repository: PetRepository,
        user_repository: UserRepository
    ):
        self._appointment_repository = appointment_repository
        self._pet_repository = pet_repository
        self._user_repository = user_repository
    
    def schedule_appointment(self, appointment_data: dict) -> Appointment:
        """
        CASO DE USO: Programar nueva cita
        """
        # Validar datos requeridos
        self._validate_appointment_data(appointment_data)
        
        # Verificar que la mascota existe
        pet = self._pet_repository.find_by_id(appointment_data['pet_id'])
        if not pet:
            raise ValueError("Pet not found")
        
        if not pet.is_active:
            raise ValueError("Cannot schedule appointment for inactive pet")
        
        # Verificar que el veterinario existe (si se especifica)
        veterinarian = None
        if appointment_data.get('veterinarian_id'):
            veterinarian = self._user_repository.find_by_id(appointment_data['veterinarian_id'])
            if not veterinarian:
                raise ValueError("Veterinarian not found")
            
            # Verificar que sea veterinario
            if veterinarian.role.value not in ['veterinarian', 'admin']:
                raise ValueError("Selected user is not a veterinarian")
        
        # Convertir fecha y hora
        appointment_date = self._parse_appointment_datetime(appointment_data['appointment_date'])
        
        # Validar que la fecha no sea en el pasado
        if appointment_date < datetime.now():
            raise ValueError("Cannot schedule appointments in the past")
        
        # Convertir tipo de cita
        appointment_type = AppointmentType(appointment_data['appointment_type'])
        
        # Calcular duración por defecto según el tipo
        duration = appointment_data.get('duration_minutes', self._get_default_duration(appointment_type))
        
        # Crear entidad cita
        appointment = Appointment(
            id=None,
            pet_id=pet.id,
            veterinarian_id=veterinarian.id if veterinarian else None,
            appointment_date=appointment_date,
            duration_minutes=duration,
            appointment_type=appointment_type,
            status=AppointmentStatus.SCHEDULED,
            reason=appointment_data.get('reason', '').strip() or None,
            notes=appointment_data.get('notes', '').strip() or None,
            created_at=datetime.now(),
            created_by=appointment_data.get('created_by')
        )
        
        # Guardar en repositorio
        return self._appointment_repository.save(appointment)
    
    def get_all_appointments(self, status_filter: Optional[AppointmentStatus] = None) -> List[Appointment]:
        """CASO DE USO: Obtener todas las citas, opcionalmente filtradas por estado"""
        if status_filter:
            return self._appointment_repository.find_by_status(status_filter)
        else:
            return self._appointment_repository.find_all()
    
    def get_appointment_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """CASO DE USO: Obtener cita por ID"""
        if not appointment_id or appointment_id <= 0:
            raise ValueError("Valid appointment ID is required")
        
        return self._appointment_repository.find_by_id(appointment_id)
    
    def get_appointments_by_date(self, target_date: date) -> List[Appointment]:
        """CASO DE USO: Obtener citas de una fecha específica"""
        return self._appointment_repository.find_by_date(target_date)
    
    def get_appointments_by_pet(self, pet_id: int) -> List[Appointment]:
        """CASO DE USO: Obtener historial de citas de una mascota"""
        pet = self._pet_repository.find_by_id(pet_id)
        if not pet:
            raise ValueError("Pet not found")
        
        return self._appointment_repository.find_by_pet_id(pet_id)
    
    def confirm_appointment(self, appointment_id: int) -> Appointment:
        """CASO DE USO: Confirmar cita programada"""
        appointment = self._appointment_repository.find_by_id(appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        
        if appointment.status != AppointmentStatus.SCHEDULED:
            raise ValueError("Only scheduled appointments can be confirmed")
        
        appointment.status = AppointmentStatus.CONFIRMED
        appointment.updated_at = datetime.now()
        
        return self._appointment_repository.update(appointment)
    
    def complete_appointment(self, appointment_id: int, completion_notes: Optional[str] = None) -> Appointment:
        """CASO DE USO: Completar cita"""
        appointment = self._appointment_repository.find_by_id(appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        
        if appointment.status != AppointmentStatus.IN_PROGRESS:
            raise ValueError("Only appointments in progress can be completed")
        
        appointment.mark_as_completed(completion_notes)
        
        return self._appointment_repository.update(appointment)
    
    def cancel_appointment(self, appointment_id: int, cancellation_reason: Optional[str] = None) -> Appointment:
        """CASO DE USO: Cancelar cita"""
        appointment = self._appointment_repository.find_by_id(appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        
        if not appointment.can_be_modified:
            raise ValueError("This appointment cannot be cancelled")
        
        appointment.cancel(cancellation_reason)
        
        return self._appointment_repository.update(appointment)
    
    def get_daily_schedule(self, target_date: date, veterinarian_id: Optional[int] = None) -> List[dict]:
        """CASO DE USO: Obtener horario del día con información completa"""
        appointments = self._appointment_repository.find_by_date(target_date)
        
        if veterinarian_id:
            appointments = [apt for apt in appointments if apt.veterinarian_id == veterinarian_id]
        
        # Enriquecer con información adicional
        schedule = []
        for appointment in appointments:
            pet = self._pet_repository.find_by_id(appointment.pet_id)
            veterinarian = None
            if appointment.veterinarian_id:
                veterinarian = self._user_repository.find_by_id(appointment.veterinarian_id)
            
            schedule.append({
                'appointment': appointment,
                'pet': pet,
                'veterinarian': veterinarian,
                'time_slot': f"{appointment.appointment_date.strftime('%H:%M')} - {appointment.end_time.strftime('%H:%M')}",
                'is_upcoming': appointment.is_upcoming
            })
        
        # Ordenar por hora
        schedule.sort(key=lambda x: x['appointment'].appointment_date)
        
        return schedule
    
    def get_availability_slots(self, date_target: date, veterinarian_id: int, duration_minutes: int = 30) -> List[dict]:
        """CASO DE USO: Obtener slots de horario disponibles para un veterinario"""
        # Horarios típicos de clínica: 8:00 AM a 6:00 PM
        start_hour = 8
        end_hour = 18
        
        # Obtener citas existentes del veterinario para esa fecha
        existing_appointments = [
            apt for apt in self._appointment_repository.find_by_date(date_target)
            if apt.veterinarian_id == veterinarian_id and apt.status in [
                AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED, AppointmentStatus.IN_PROGRESS
            ]
        ]
        
        available_slots = []
        current_time = datetime.combine(date_target, datetime.min.time().replace(hour=start_hour))
        end_time = datetime.combine(date_target, datetime.min.time().replace(hour=end_hour))
        
        while current_time + timedelta(minutes=duration_minutes) <= end_time:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            # Verificar si este slot está libre
            is_available = True
            for appointment in existing_appointments:
                if (current_time < appointment.end_time and 
                    slot_end > appointment.appointment_date):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    'start_time': current_time,
                    'end_time': slot_end,
                    'display_time': f"{current_time.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
                })
            
            # Avanzar a la siguiente slot (cada 30 minutos)
            current_time += timedelta(minutes=30)
        
        return available_slots
    
    def _validate_appointment_data(self, appointment_data: dict):
        """Valida los datos de la cita"""
        required_fields = ['pet_id', 'appointment_date', 'appointment_type']
        
        for field in required_fields:
            if not appointment_data.get(field):
                raise ValueError(f"{field} is required")
        
        # Validar tipo de cita
        try:
            AppointmentType(appointment_data['appointment_type'])
        except ValueError:
            valid_types = [t.value for t in AppointmentType]
            raise ValueError(f"Invalid appointment type. Valid options: {valid_types}")
        
        # Validar duración si se proporciona
        if 'duration_minutes' in appointment_data:
            duration = appointment_data['duration_minutes']
            if not isinstance(duration, int) or duration <= 0 or duration > 480:
                raise ValueError("Duration must be between 1 and 480 minutes")
    
    def _parse_appointment_datetime(self, date_input) -> datetime:
        """Convierte entrada de fecha/hora a datetime"""
        if isinstance(date_input, datetime):
            return date_input
        elif isinstance(date_input, str):
            try:
                # Intentar varios formatos
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M']:
                    try:
                        return datetime.strptime(date_input, fmt)
                    except ValueError:
                        continue
                raise ValueError("Invalid date format")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD HH:MM format")
        else:
            raise ValueError("Date must be datetime object or string")
    
    def _get_default_duration(self, appointment_type: AppointmentType) -> int:
        """Retorna duración por defecto según el tipo de cita"""
        duration_map = {
            AppointmentType.CONSULTATION: 30,
            AppointmentType.VACCINATION: 15,
            AppointmentType.SURGERY: 120,
            AppointmentType.EMERGENCY: 60,
            AppointmentType.FOLLOW_UP: 20,
            AppointmentType.GROOMING: 60
        }
        
        return duration_map.get(appointment_type, 30)
    
    def start_appointment(self, appointment_id: int) -> Appointment:
        """
        Inicia una cita confirmada (cambia estado a 'in_progress')
        
        Args:
            appointment_id: ID de la cita a iniciar
            
        Returns:
            Appointment: La cita actualizada
            
        Raises:
            ValueError: Si la cita no existe o no se puede iniciar
        """
        appointment = self._appointment_repository.find_by_id(appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        
        if appointment.status != AppointmentStatus.CONFIRMED:
            raise ValueError("Only confirmed appointments can be started")
        
        # Actualizar estado
        appointment.status = AppointmentStatus.IN_PROGRESS
        appointment.updated_at = datetime.now()
        
        # Guardar cambios
        updated_appointment = self._appointment_repository.update(appointment)
        
        return updated_appointment
    
    def update_appointment(self, appointment_id: int, update_data: dict) -> Appointment:
        """
        Actualiza los datos de una cita existente
        """
        appointment = self._appointment_repository.find_by_id(appointment_id)
        if not appointment:
            raise ValueError("Appointment not found")
        
        try:
            # Validar que no se esté moviendo a una fecha pasada (solo si se cambia la fecha)
            if 'appointment_date' in update_data:
                new_date = update_data['appointment_date']
                if new_date.replace(tzinfo=None) < datetime.now():
                    raise ValueError("Cannot reschedule to past date")
            
            # Convertir appointment_type si viene como string
            if 'appointment_type' in update_data:
                if isinstance(update_data['appointment_type'], str):
                    update_data['appointment_type'] = AppointmentType(update_data['appointment_type'])
            
            # Actualizar campos
            for field, value in update_data.items():
                if hasattr(appointment, field) and value is not None:
                    setattr(appointment, field, value)
            
            # Actualizar timestamp
            appointment.updated_at = datetime.now()
            
            # Guardar cambios
            updated_appointment = self._appointment_repository.update(appointment)
            
            return updated_appointment
            
        except Exception as e:
            print(f"Error in update_appointment: {e}")
            raise e