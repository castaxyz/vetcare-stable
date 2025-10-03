"""
EXPLICACIÓN: Implementación concreta del AppointmentRepository usando SQLAlchemy.
Maneja persistencia de citas con búsquedas complejas y verificación de disponibilidad.
"""

from typing import List, Optional
from datetime import datetime, date, time
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError

from domain.entities.appointment import Appointment, AppointmentStatus, AppointmentType
from interfaces.repositories.appointment_repository import AppointmentRepository
from infra.database.models import AppointmentModel, AppointmentStatusEnum, AppointmentTypeEnum
from infra.database import get_db_session

class SQLAppointmentRepository(AppointmentRepository):
    """
    Implementación SQLAlchemy del repositorio de citas.
    Maneja persistencia y búsquedas complejas de citas veterinarias.
    """
    
    def __init__(self):
        self._session_factory = get_db_session
    
    def save(self, appointment: Appointment) -> Appointment:
        """Guarda una cita en la base de datos"""
        session = self._session_factory()
        try:
            if appointment.id is None:
                # Crear nueva cita
                appointment_model = self._entity_to_model(appointment)
                session.add(appointment_model)
                session.flush()
                appointment.id = appointment_model.id
            else:
                # Actualizar cita existente
                appointment_model = session.query(AppointmentModel).filter(
                    AppointmentModel.id == appointment.id
                ).first()
                if not appointment_model:
                    raise ValueError(f"Appointment with ID {appointment.id} not found")
                
                self._update_model_from_entity(appointment_model, appointment)
            
            session.commit()
            return appointment
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_by_id(self, appointment_id: int) -> Optional[Appointment]:
        """Busca cita por ID"""
        session = self._session_factory()
        try:
            appointment_model = session.query(AppointmentModel).filter(
                AppointmentModel.id == appointment_id
            ).first()
            return self._model_to_entity(appointment_model) if appointment_model else None
        finally:
            session.close()
    
    def find_all(self) -> List[Appointment]:
        """Obtiene todas las citas"""
        session = self._session_factory()
        try:
            appointment_models = session.query(AppointmentModel).order_by(
                AppointmentModel.appointment_date.desc()
            ).all()
            return [self._model_to_entity(model) for model in appointment_models]
        finally:
            session.close()
    
    def find_by_pet_id(self, pet_id: int) -> List[Appointment]:
        """Busca citas de una mascota específica"""
        session = self._session_factory()
        try:
            appointment_models = session.query(AppointmentModel).filter(
                AppointmentModel.pet_id == pet_id
            ).order_by(AppointmentModel.appointment_date.desc()).all()
            return [self._model_to_entity(model) for model in appointment_models]
        finally:
            session.close()
    
    def find_by_veterinarian_id(self, veterinarian_id: int) -> List[Appointment]:
        """Busca citas de un veterinario específico"""
        session = self._session_factory()
        try:
            appointment_models = session.query(AppointmentModel).filter(
                AppointmentModel.veterinarian_id == veterinarian_id
            ).order_by(AppointmentModel.appointment_date.desc()).all()
            return [self._model_to_entity(model) for model in appointment_models]
        finally:
            session.close()
    
    def find_by_date(self, appointment_date: date) -> List[Appointment]:
        """Busca citas de una fecha específica"""
        session = self._session_factory()
        try:
            # Crear rango de fecha (inicio y fin del día)
            start_datetime = datetime.combine(appointment_date, time.min)
            end_datetime = datetime.combine(appointment_date, time.max)
            
            appointment_models = session.query(AppointmentModel).filter(
                and_(
                    AppointmentModel.appointment_date >= start_datetime,
                    AppointmentModel.appointment_date <= end_datetime
                )
            ).order_by(AppointmentModel.appointment_date).all()
            
            return [self._model_to_entity(model) for model in appointment_models]
        finally:
            session.close()
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Appointment]:
        """Busca citas en un rango de fechas"""
        session = self._session_factory()
        try:
            appointment_models = session.query(AppointmentModel).filter(
                and_(
                    AppointmentModel.appointment_date >= start_date,
                    AppointmentModel.appointment_date <= end_date
                )
            ).order_by(AppointmentModel.appointment_date).all()
            
            return [self._model_to_entity(model) for model in appointment_models]
        finally:
            session.close()
    
    def find_by_status(self, status: AppointmentStatus) -> List[Appointment]:
        """Busca citas por estado"""
        session = self._session_factory()
        try:
            appointment_models = session.query(AppointmentModel).filter(
                AppointmentModel.status == AppointmentStatusEnum(status.value)
            ).order_by(AppointmentModel.appointment_date).all()
            
            return [self._model_to_entity(model) for model in appointment_models]
        finally:
            session.close()
    
    def update(self, appointment: Appointment) -> Appointment:
        """Actualiza una cita existente"""
        if not appointment.id:
            raise ValueError("Cannot update appointment without ID")
        return self.save(appointment)
    
    def delete(self, appointment_id: int) -> bool:
        """Elimina una cita por ID"""
        session = self._session_factory()
        try:
            appointment_model = session.query(AppointmentModel).filter(
                AppointmentModel.id == appointment_id
            ).first()
            if not appointment_model:
                return False
            
            session.delete(appointment_model)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_upcoming_appointments(self, hours: int = 24) -> List[Appointment]:
        """Busca citas próximas"""
        session = self._session_factory()
        try:
            now = datetime.now()
            future_limit = now + timedelta(hours=hours)
            
            appointment_models = session.query(AppointmentModel).filter(
                and_(
                    AppointmentModel.appointment_date >= now,
                    AppointmentModel.appointment_date <= future_limit,
                    AppointmentModel.status.in_([
                        AppointmentStatusEnum.SCHEDULED,
                        AppointmentStatusEnum.CONFIRMED
                    ])
                )
            ).order_by(AppointmentModel.appointment_date).all()
            
            return [self._model_to_entity(model) for model in appointment_models]
        finally:
            session.close()
    
    def check_availability(self, start_time: datetime, end_time: datetime, veterinarian_id: int) -> bool:
        """
        Verifica disponibilidad de horario para un veterinario.
        Retorna True si el horario está disponible, False si hay conflictos.
        """
        session = self._session_factory()
        try:
            # Buscar citas que se solapen con el horario propuesto
            overlapping_appointments = session.query(AppointmentModel).filter(
                and_(
                    AppointmentModel.veterinarian_id == veterinarian_id,
                    AppointmentModel.status.in_([
                        AppointmentStatusEnum.SCHEDULED,
                        AppointmentStatusEnum.CONFIRMED,
                        AppointmentStatusEnum.IN_PROGRESS
                    ]),
                    or_(
                        # Caso 1: La cita nueva empieza durante una existente
                        and_(
                            AppointmentModel.appointment_date <= start_time,
                            func.datetime(
                                AppointmentModel.appointment_date, 
                                '+' + func.cast(AppointmentModel.duration_minutes, str) + ' minutes'
                            ) > start_time
                        ),
                        # Caso 2: La cita nueva termina durante una existente
                        and_(
                            AppointmentModel.appointment_date < end_time,
                            func.datetime(
                                AppointmentModel.appointment_date, 
                                '+' + func.cast(AppointmentModel.duration_minutes, str) + ' minutes'
                            ) >= end_time
                        ),
                        # Caso 3: La cita nueva contiene completamente una existente
                        and_(
                            AppointmentModel.appointment_date >= start_time,
                            func.datetime(
                                AppointmentModel.appointment_date, 
                                '+' + func.cast(AppointmentModel.duration_minutes, str) + ' minutes'
                            ) <= end_time
                        )
                    )
                )
            ).first()
            
            # Si no hay citas que se solapen, el horario está disponible
            return overlapping_appointments is None
            
        finally:
            session.close()
    
    def _entity_to_model(self, appointment: Appointment) -> AppointmentModel:
        """Convierte entidad de dominio a modelo SQLAlchemy"""
        return AppointmentModel(
            id=appointment.id,
            pet_id=appointment.pet_id,
            veterinarian_id=appointment.veterinarian_id,
            appointment_date=appointment.appointment_date,
            duration_minutes=appointment.duration_minutes,
            appointment_type=AppointmentTypeEnum(appointment.appointment_type.value),
            status=AppointmentStatusEnum(appointment.status.value),
            reason=appointment.reason,
            notes=appointment.notes,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at,
            created_by=appointment.created_by
        )
    
    def _model_to_entity(self, model: AppointmentModel) -> Appointment:
        """Convierte modelo SQLAlchemy a entidad de dominio"""
        return Appointment(
            id=model.id,
            pet_id=model.pet_id,
            veterinarian_id=model.veterinarian_id,
            appointment_date=model.appointment_date,
            duration_minutes=model.duration_minutes,
            appointment_type=AppointmentType(model.appointment_type.value),
            status=AppointmentStatus(model.status.value),
            reason=model.reason,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by
        )
    
    def _update_model_from_entity(self, model: AppointmentModel, entity: Appointment):
        """Actualiza modelo SQLAlchemy con datos de entidad"""
        model.pet_id = entity.pet_id
        model.veterinarian_id = entity.veterinarian_id
        model.appointment_date = entity.appointment_date
        model.duration_minutes = entity.duration_minutes
        model.appointment_type = AppointmentTypeEnum(entity.appointment_type.value)
        model.status = AppointmentStatusEnum(entity.status.value)
        model.reason = entity.reason
        model.notes = entity.notes
        model.updated_at = entity.updated_at
        model.created_by = entity.created_by