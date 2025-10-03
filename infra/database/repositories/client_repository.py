"""
EXPLICACIÓN: Implementación concreta del ClientRepository usando SQLAlchemy.
Implementa operaciones de persistencia para clientes con búsquedas optimizadas.
"""

from typing import List, Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError

from domain.entities.client import Client
from interfaces.repositories.client_repository import ClientRepository
from infra.database.models import ClientModel
from infra.database import get_db_session

class SQLClientRepository(ClientRepository):
    """
    Implementación SQLAlchemy del repositorio de clientes.
    Maneja persistencia y búsquedas de propietarios de mascotas.
    """
    
    def __init__(self):
        self._session_factory = get_db_session
    
    def save(self, client: Client) -> Client:
        """Guarda un cliente en la base de datos"""
        session = self._session_factory()
        try:
            if client.id is None:
                # Crear nuevo cliente
                client_model = self._entity_to_model(client)
                session.add(client_model)
                session.flush()
                client.id = client_model.id
            else:
                # Actualizar cliente existente
                client_model = session.query(ClientModel).filter(
                    ClientModel.id == client.id
                ).first()
                if not client_model:
                    raise ValueError(f"Client with ID {client.id} not found")
                
                self._update_model_from_entity(client_model, client)
            
            session.commit()
            return client
            
        except IntegrityError as e:
            session.rollback()
            if 'email' in str(e):
                raise ValueError("Email already exists")
            elif 'identification_number' in str(e):
                raise ValueError("Identification number already exists")
            else:
                raise ValueError("Integrity constraint violation")
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_by_id(self, client_id: int) -> Optional[Client]:
        """Busca cliente por ID"""
        session = self._session_factory()
        try:
            client_model = session.query(ClientModel).filter(
                ClientModel.id == client_id
            ).first()
            return self._model_to_entity(client_model) if client_model else None
        finally:
            session.close()
    
    def find_all(self) -> List[Client]:
        """Obtiene todos los clientes"""
        session = self._session_factory()
        try:
            client_models = session.query(ClientModel).order_by(
                ClientModel.last_name, ClientModel.first_name
            ).all()
            return [self._model_to_entity(model) for model in client_models]
        finally:
            session.close()
    
    def find_by_name(self, first_name: str, last_name: str) -> List[Client]:
        """Busca clientes por nombre"""
        session = self._session_factory()
        try:
            client_models = session.query(ClientModel).filter(
                and_(
                    ClientModel.first_name.ilike(f'%{first_name}%'),
                    ClientModel.last_name.ilike(f'%{last_name}%')
                )
            ).all()
            return [self._model_to_entity(model) for model in client_models]
        finally:
            session.close()
    
    def find_by_email(self, email: str) -> Optional[Client]:
        """Busca cliente por email"""
        session = self._session_factory()
        try:
            client_model = session.query(ClientModel).filter(
                ClientModel.email == email
            ).first()
            return self._model_to_entity(client_model) if client_model else None
        finally:
            session.close()
    
    def find_by_identification(self, identification: str) -> Optional[Client]:
        """Busca cliente por número de identificación"""
        session = self._session_factory()
        try:
            client_model = session.query(ClientModel).filter(
                ClientModel.identification_number == identification
            ).first()
            return self._model_to_entity(client_model) if client_model else None
        finally:
            session.close()
    
    def update(self, client: Client) -> Client:
        """Actualiza un cliente existente"""
        if not client.id:
            raise ValueError("Cannot update client without ID")
        return self.save(client)
    
    def delete(self, client_id: int) -> bool:
        """Elimina un cliente por ID"""
        session = self._session_factory()
        try:
            client_model = session.query(ClientModel).filter(
                ClientModel.id == client_id
            ).first()
            if not client_model:
                return False
            
            session.delete(client_model)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def search(self, query: str) -> List[Client]:
        """
        Busca clientes por término de búsqueda general.
        Busca en nombres, email y número de identificación.
        """
        session = self._session_factory()
        try:
            # Búsqueda en múltiples campos
            client_models = session.query(ClientModel).filter(
                or_(
                    ClientModel.first_name.ilike(f'%{query}%'),
                    ClientModel.last_name.ilike(f'%{query}%'),
                    ClientModel.email.ilike(f'%{query}%'),
                    ClientModel.identification_number.ilike(f'%{query}%'),
                    ClientModel.phone.ilike(f'%{query}%')
                )
            ).order_by(ClientModel.last_name, ClientModel.first_name).all()
            
            return [self._model_to_entity(model) for model in client_models]
        finally:
            session.close()
    
    def _entity_to_model(self, client: Client) -> ClientModel:
        """Convierte entidad de dominio a modelo SQLAlchemy"""
        return ClientModel(
            id=client.id,
            first_name=client.first_name,
            last_name=client.last_name,
            email=client.email,
            phone=client.phone,
            address=client.address,
            identification_number=client.identification_number,
            created_at=client.created_at,
            updated_at=client.updated_at
        )
    
    def _model_to_entity(self, model: ClientModel) -> Client:
        """Convierte modelo SQLAlchemy a entidad de dominio"""
        return Client(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            phone=model.phone,
            address=model.address,
            identification_number=model.identification_number,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _update_model_from_entity(self, model: ClientModel, entity: Client):
        """Actualiza modelo SQLAlchemy con datos de entidad"""
        model.first_name = entity.first_name
        model.last_name = entity.last_name
        model.email = entity.email
        model.phone = entity.phone
        model.address = entity.address
        model.identification_number = entity.identification_number
        model.updated_at = entity.updated_at