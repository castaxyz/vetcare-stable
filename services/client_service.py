"""
EXPLICACIÓN: Service que maneja la lógica de negocio relacionada con clientes.
Coordina las operaciones CRUD y validaciones de clientes.
"""

from typing import List, Optional
from datetime import datetime

from domain.entities.client import Client
from domain.value_objects.email import Email
from interfaces.repositories.client_repository import ClientRepository

class ClientService:
    """
    Servicio para gestión de clientes.
    Maneja casos de uso relacionados con propietarios de mascotas.
    """
    
    def __init__(self, client_repository: ClientRepository):
        self._client_repository = client_repository
    
    def create_client(self, client_data: dict) -> Client:
        """
        CASO DE USO: Crear nuevo cliente
        
        Args:
            client_data: Diccionario con datos del cliente
            
        Returns:
            Client creado
            
        Raises:
            ValueError: Si los datos son inválidos o ya existe el cliente
        """
        # Validar datos requeridos
        self._validate_client_data(client_data)
        
        # Validar email si se proporciona
        email_value = None
        if client_data.get('email'):
            email = Email(client_data['email'])
            email_value = email.value
            
            # Verificar que no exista otro cliente con el mismo email
            existing_client = self._client_repository.find_by_email(email_value)
            if existing_client:
                raise ValueError("A client with this email already exists")
        
        # Verificar identificación única si se proporciona
        if client_data.get('identification_number'):
            existing_client = self._client_repository.find_by_identification(
                client_data['identification_number']
            )
            if existing_client:
                raise ValueError("A client with this identification number already exists")
        
        # Crear entidad cliente
        client = Client(
            id=None,
            first_name=client_data['first_name'].strip(),
            last_name=client_data['last_name'].strip(),
            email=email_value,
            phone=client_data.get('phone', '').strip() or None,
            address=client_data.get('address', '').strip() or None,
            identification_number=client_data.get('identification_number', '').strip() or None,
            created_at=datetime.utcnow()
        )
        
        # Guardar en repositorio
        return self._client_repository.save(client)
    
    def get_all_clients(self) -> List[Client]:
        """
        CASO DE USO: Obtener todos los clientes
        """
        return self._client_repository.find_all()
    
    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        """
        CASO DE USO: Obtener cliente por ID
        """
        if not client_id or client_id <= 0:
            raise ValueError("Valid client ID is required")
        
        return self._client_repository.find_by_id(client_id)
    
    def update_client(self, client_id: int, client_data: dict) -> Client:
        """
        CASO DE USO: Actualizar datos de cliente
        """
        # Buscar cliente existente
        existing_client = self._client_repository.find_by_id(client_id)
        if not existing_client:
            raise ValueError("Client not found")
        
        # Validar datos
        self._validate_client_data(client_data, is_update=True)
        
        # Validar email si se proporciona y es diferente al actual
        if client_data.get('email') and client_data['email'] != existing_client.email:
            email = Email(client_data['email'])
            other_client = self._client_repository.find_by_email(email.value)
            if other_client and other_client.id != client_id:
                raise ValueError("Another client with this email already exists")
            existing_client.email = email.value
        
        # Actualizar campos
        if client_data.get('first_name'):
            existing_client.first_name = client_data['first_name'].strip()
        if client_data.get('last_name'):
            existing_client.last_name = client_data['last_name'].strip()
        if 'phone' in client_data:
            existing_client.phone = client_data['phone']
        if 'address' in client_data:
            existing_client.address = client_data['address']
        if 'identification_number' in client_data:
            existing_client.identification_number = client_data['identification_number']
        
        existing_client.updated_at = datetime.utcnow()
        
        # Guardar cambios
        return self._client_repository.update(existing_client)
    
    def delete_client(self, client_id: int) -> bool:
        """
        CASO DE USO: Eliminar cliente
        """
        client = self._client_repository.find_by_id(client_id)
        if not client:
            raise ValueError("Client not found")
        
        return self._client_repository.delete(client_id)
    
    def search_clients(self, query: str) -> List[Client]:
        """
        CASO DE USO: Buscar clientes por término de búsqueda
        """
        if not query or len(query.strip()) < 2:
            return []
        
        return self._client_repository.search(query.strip())
    
    def get_client_summary(self, client_id: int) -> dict:
        """
        CASO DE USO: Obtener resumen completo del cliente
        """
        client = self.get_client_by_id(client_id)
        if not client:
            raise ValueError("Client not found")
        
        return {
            'client': client,
            'full_name': client.full_name,
            'contact_info': client.display_contact,
            'has_complete_contact': client.has_complete_contact_info(),
        }
    
    def _validate_client_data(self, client_data: dict, is_update: bool = False):
        """Valida los datos del cliente"""
        # En creación, nombres son obligatorios
        if not is_update:
            if not client_data.get('first_name', '').strip():
                raise ValueError("First name is required")
            if not client_data.get('last_name', '').strip():
                raise ValueError("Last name is required")
        
        # Validar longitud de nombres
        if client_data.get('first_name') and len(client_data['first_name'].strip()) < 2:
            raise ValueError("First name must be at least 2 characters long")
        
        if client_data.get('last_name') and len(client_data['last_name'].strip()) < 2:
            raise ValueError("Last name must be at least 2 characters long")
        
        # Validar teléfono si se proporciona
        if client_data.get('phone'):
            phone = client_data['phone'].strip()
            if phone and len(phone) < 7:
                raise ValueError("Phone number must be at least 7 digits long")