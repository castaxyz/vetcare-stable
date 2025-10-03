"""
EXPLICACIÓN: Implementación concreta del UserRepository usando SQLAlchemy.
Implementa todas las operaciones definidas en la interfaz del dominio.
Esta clase es la que realmente interactúa con la base de datos.
"""

from typing import List, Optional
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from domain.entities.user import User, UserRole
from interfaces.repositories.user_repository import UserRepository
from infra.database.models import UserModel, UserRoleEnum
from infra.database import get_db_session

class SQLUserRepository(UserRepository):
    """
    Implementación SQLAlchemy del repositorio de usuarios.
    Maneja toda la persistencia de usuarios en la base de datos.
    """
    
    def __init__(self):
        self._session_factory = get_db_session
    
    def save(self, user: User) -> User:
        """
        Guarda un usuario en la base de datos.
        Si tiene ID, actualiza; si no, crea nuevo.
        """
        session = self._session_factory()
        try:
            if user.id is None:
                # Crear nuevo usuario
                user_model = self._entity_to_model(user)
                session.add(user_model)
                session.flush()  # Para obtener el ID generado
                user.id = user_model.id
            else:
                # Actualizar usuario existente
                user_model = session.query(UserModel).filter(UserModel.id == user.id).first()
                if not user_model:
                    raise ValueError(f"User with ID {user.id} not found")
                
                self._update_model_from_entity(user_model, user)
            
            session.commit()
            return user
            
        except IntegrityError as e:
            session.rollback()
            if 'username' in str(e):
                raise ValueError("Username already exists")
            elif 'email' in str(e):
                raise ValueError("Email already exists")
            else:
                raise ValueError("Integrity constraint violation")
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuario por ID"""
        session = self._session_factory()
        try:
            user_model = session.query(UserModel).filter(UserModel.id == user_id).first()
            return self._model_to_entity(user_model) if user_model else None
        finally:
            session.close()
    
    def find_by_username(self, username: str) -> Optional[User]:
        """Busca usuario por nombre de usuario"""
        session = self._session_factory()
        try:
            user_model = session.query(UserModel).filter(
                UserModel.username == username
            ).first()
            return self._model_to_entity(user_model) if user_model else None
        finally:
            session.close()
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Busca usuario por email"""
        session = self._session_factory()
        try:
            user_model = session.query(UserModel).filter(
                UserModel.email == email
            ).first()
            return self._model_to_entity(user_model) if user_model else None
        finally:
            session.close()
    
    def find_all(self) -> List[User]:
        """Obtiene todos los usuarios"""
        session = self._session_factory()
        try:
            user_models = session.query(UserModel).order_by(UserModel.created_at.desc()).all()
            return [self._model_to_entity(model) for model in user_models]
        finally:
            session.close()
    
    def update(self, user: User) -> User:
        """Actualiza un usuario existente"""
        if not user.id:
            raise ValueError("Cannot update user without ID")
        
        return self.save(user)
    
    def delete(self, user_id: int) -> bool:
        """Elimina un usuario por ID"""
        session = self._session_factory()
        try:
            user_model = session.query(UserModel).filter(UserModel.id == user_id).first()
            if not user_model:
                return False
            
            session.delete(user_model)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def exists_username(self, username: str) -> bool:
        """Verifica si existe un usuario con ese username"""
        session = self._session_factory()
        try:
            exists = session.query(UserModel).filter(
                UserModel.username == username
            ).first() is not None
            return exists
        finally:
            session.close()
    
    def exists_email(self, email: str) -> bool:
        """Verifica si existe un usuario con ese email"""
        session = self._session_factory()
        try:
            exists = session.query(UserModel).filter(
                UserModel.email == email
            ).first() is not None
            return exists
        finally:
            session.close()
    
    def _entity_to_model(self, user: User) -> UserModel:
        """Convierte entidad de dominio a modelo SQLAlchemy"""
        return UserModel(
            id=user.id,
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            role=UserRoleEnum(user.role.value),
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            failed_login_attempts=user.failed_login_attempts,
            locked_until=user.locked_until
        )
    
    def _model_to_entity(self, model: UserModel) -> User:
        """Convierte modelo SQLAlchemy a entidad de dominio"""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            role=UserRole(model.role.value),
            first_name=model.first_name,
            last_name=model.last_name,
            is_active=model.is_active,
            created_at=model.created_at,
            last_login=model.last_login,
            failed_login_attempts=model.failed_login_attempts,
            locked_until=model.locked_until
        )
    
    def _update_model_from_entity(self, model: UserModel, entity: User):
        """Actualiza modelo SQLAlchemy con datos de entidad"""
        model.username = entity.username
        model.email = entity.email
        model.password_hash = entity.password_hash
        model.role = UserRoleEnum(entity.role.value)
        model.first_name = entity.first_name
        model.last_name = entity.last_name
        model.is_active = entity.is_active
        model.last_login = entity.last_login
        model.failed_login_attempts = entity.failed_login_attempts
        model.locked_until = entity.locked_until