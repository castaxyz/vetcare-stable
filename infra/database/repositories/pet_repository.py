"""
EXPLICACIÓN: Implementación concreta del PetRepository usando SQLAlchemy.
Maneja persistencia de mascotas con búsquedas optimizadas y joins con clientes.
"""

from typing import List, Optional
from sqlalchemy.orm import sessionmaker, joinedload
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from domain.entities.pet import Pet, PetGender, PetSpecies
from interfaces.repositories.pet_repository import PetRepository
from infra.database.models import PetModel, PetSpeciesEnum, PetGenderEnum
from infra.database import get_db_session

class SQLPetRepository(PetRepository):
    """
    Implementación SQLAlchemy del repositorio de mascotas.
    Maneja persistencia y búsquedas de mascotas con optimizaciones.
    """
    
    def __init__(self):
        self._session_factory = get_db_session
    
    def save(self, pet: Pet) -> Pet:
        """Guarda una mascota en la base de datos"""
        session = self._session_factory()
        try:
            if pet.id is None:
                # Crear nueva mascota
                pet_model = self._entity_to_model(pet)
                session.add(pet_model)
                session.flush()
                pet.id = pet_model.id
            else:
                # Actualizar mascota existente
                pet_model = session.query(PetModel).filter(
                    PetModel.id == pet.id
                ).first()
                if not pet_model:
                    raise ValueError(f"Pet with ID {pet.id} not found")
                
                self._update_model_from_entity(pet_model, pet)
            
            session.commit()
            return pet
            
        except IntegrityError as e:
            session.rollback()
            if 'microchip_number' in str(e):
                raise ValueError("Microchip number already exists")
            else:
                raise ValueError("Integrity constraint violation")
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_by_id(self, pet_id: int) -> Optional[Pet]:
        """Busca mascota por ID"""
        session = self._session_factory()
        try:
            pet_model = session.query(PetModel).filter(
                PetModel.id == pet_id
            ).first()
            return self._model_to_entity(pet_model) if pet_model else None
        finally:
            session.close()
    
    def find_all(self) -> List[Pet]:
        """Obtiene todas las mascotas"""
        session = self._session_factory()
        try:
            pet_models = session.query(PetModel).order_by(PetModel.name).all()
            return [self._model_to_entity(model) for model in pet_models]
        finally:
            session.close()
    
    def find_by_client_id(self, client_id: int) -> List[Pet]:
        """Busca mascotas de un cliente específico"""
        session = self._session_factory()
        try:
            pet_models = session.query(PetModel).filter(
                PetModel.client_id == client_id
            ).order_by(PetModel.name).all()
            return [self._model_to_entity(model) for model in pet_models]
        finally:
            session.close()
    
    def find_by_name(self, name: str) -> List[Pet]:
        """Busca mascotas por nombre"""
        session = self._session_factory()
        try:
            pet_models = session.query(PetModel).filter(
                PetModel.name.ilike(f'%{name}%')
            ).order_by(PetModel.name).all()
            return [self._model_to_entity(model) for model in pet_models]
        finally:
            session.close()
    
    def find_by_microchip(self, microchip: str) -> Optional[Pet]:
        """Busca mascota por microchip"""
        session = self._session_factory()
        try:
            pet_model = session.query(PetModel).filter(
                PetModel.microchip_number == microchip
            ).first()
            return self._model_to_entity(pet_model) if pet_model else None
        finally:
            session.close()
    
    def update(self, pet: Pet) -> Pet:
        """Actualiza una mascota existente"""
        if not pet.id:
            raise ValueError("Cannot update pet without ID")
        return self.save(pet)
    
    def delete(self, pet_id: int) -> bool:
        """Elimina una mascota por ID"""
        session = self._session_factory()
        try:
            pet_model = session.query(PetModel).filter(
                PetModel.id == pet_id
            ).first()
            if not pet_model:
                return False
            
            session.delete(pet_model)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_active_pets(self) -> List[Pet]:
        """Retorna solo mascotas activas"""
        session = self._session_factory()
        try:
            pet_models = session.query(PetModel).filter(
                PetModel.is_active == True
            ).order_by(PetModel.name).all()
            return [self._model_to_entity(model) for model in pet_models]
        finally:
            session.close()
    
    def _entity_to_model(self, pet: Pet) -> PetModel:
        """Convierte entidad de dominio a modelo SQLAlchemy"""
        return PetModel(
            id=pet.id,
            name=pet.name,
            species=PetSpeciesEnum(pet.species.value),
            breed=pet.breed,
            birth_date=pet.birth_date,
            gender=PetGenderEnum(pet.gender.value),
            color=pet.color,
            weight=pet.weight,
            microchip_number=pet.microchip_number,
            client_id=pet.client_id,
            is_active=pet.is_active,
            created_at=pet.created_at,
            updated_at=pet.updated_at
        )
    
    def _model_to_entity(self, model: PetModel) -> Pet:
        """Convierte modelo SQLAlchemy a entidad de dominio"""
        return Pet(
            id=model.id,
            name=model.name,
            species=PetSpecies(model.species.value),
            breed=model.breed,
            birth_date=model.birth_date,
            gender=PetGender(model.gender.value),
            color=model.color,
            weight=model.weight,
            microchip_number=model.microchip_number,
            client_id=model.client_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _update_model_from_entity(self, model: PetModel, entity: Pet):
        """Actualiza modelo SQLAlchemy con datos de entidad"""
        model.name = entity.name
        model.species = PetSpeciesEnum(entity.species.value)
        model.breed = entity.breed
        model.birth_date = entity.birth_date
        model.gender = PetGenderEnum(entity.gender.value)
        model.color = entity.color
        model.weight = entity.weight
        model.microchip_number = entity.microchip_number
        model.client_id = entity.client_id
        model.is_active = entity.is_active
        model.updated_at = entity.updated_at