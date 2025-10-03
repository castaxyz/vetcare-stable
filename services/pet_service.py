"""
EXPLICACIÓN: Service que maneja la lógica de negocio de mascotas.
Coordina operaciones CRUD y validaciones específicas de mascotas.
"""

from typing import List, Optional
from datetime import datetime, date

from domain.entities.pet import Pet, PetGender, PetSpecies
from interfaces.repositories.pet_repository import PetRepository
from interfaces.repositories.client_repository import ClientRepository

class PetService:
    """
    Servicio para gestión de mascotas.
    Maneja casos de uso relacionados con las mascotas de los clientes.
    """
    
    def __init__(self, pet_repository: PetRepository, client_repository: ClientRepository):
        self._pet_repository = pet_repository
        self._client_repository = client_repository
    
    def create_pet(self, pet_data: dict) -> Pet:
        """
        CASO DE USO: Registrar nueva mascota
        """
        # Validar datos requeridos
        self._validate_pet_data(pet_data)
        
        # Verificar que el cliente existe
        client = self._client_repository.find_by_id(pet_data['client_id'])
        if not client:
            raise ValueError("Client not found")
        
        # Verificar microchip único si se proporciona
        if pet_data.get('microchip_number'):
            existing_pet = self._pet_repository.find_by_microchip(pet_data['microchip_number'])
            if existing_pet:
                raise ValueError("A pet with this microchip already exists")
        
        # Convertir enums
        species = PetSpecies(pet_data['species']) if pet_data.get('species') else PetSpecies.OTHER
        gender = PetGender(pet_data['gender']) if pet_data.get('gender') else PetGender.UNKNOWN
        
        # Convertir fecha de nacimiento
        birth_date = None
        if pet_data.get('birth_date'):
            if isinstance(pet_data['birth_date'], str):
                birth_date = datetime.strptime(pet_data['birth_date'], '%Y-%m-%d').date()
            elif isinstance(pet_data['birth_date'], date):
                birth_date = pet_data['birth_date']
        
        # Crear entidad mascota
        pet = Pet(
            id=None,
            name=pet_data['name'].strip(),
            species=species,
            breed=pet_data.get('breed', '').strip() or None,
            birth_date=birth_date,
            gender=gender,
            color=pet_data.get('color', '').strip() or None,
            weight=pet_data.get('weight'),
            microchip_number=(pet_data.get('microchip_number') or '').strip() or None,
            client_id=pet_data['client_id'],
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        # Guardar en repositorio
        return self._pet_repository.save(pet)
    
    def get_all_pets(self, active_only: bool = True) -> List[Pet]:
        """CASO DE USO: Obtener todas las mascotas"""
        if active_only:
            return self._pet_repository.find_active_pets()
        else:
            return self._pet_repository.find_all()
    
    def get_pet_by_id(self, pet_id: int) -> Optional[Pet]:
        """CASO DE USO: Obtener mascota por ID"""
        if not pet_id or pet_id <= 0:
            raise ValueError("Valid pet ID is required")
        
        return self._pet_repository.find_by_id(pet_id)
    
    def get_pets_by_client(self, client_id: int) -> List[Pet]:
        """CASO DE USO: Obtener mascotas de un cliente específico"""
        if not client_id or client_id <= 0:
            raise ValueError("Valid client ID is required")
        
        # Verificar que el cliente existe
        client = self._client_repository.find_by_id(client_id)
        if not client:
            raise ValueError("Client not found")
        
        return self._pet_repository.find_by_client_id(client_id)
    
    def update_pet(self, pet_id: int, pet_data: dict) -> Pet:
        """CASO DE USO: Actualizar datos de mascota"""
        # Buscar mascota existente
        existing_pet = self._pet_repository.find_by_id(pet_id)
        if not existing_pet:
            raise ValueError("Pet not found")
        
        # Validar datos (permitir actualizaciones parciales)
        self._validate_pet_data(pet_data, is_update=True)
        
        # Actualizar campos
        if pet_data.get('name'):
            existing_pet.name = pet_data['name'].strip()
        
        if pet_data.get('species'):
            existing_pet.species = PetSpecies(pet_data['species'])
        
        if pet_data.get('breed'):
            existing_pet.breed = pet_data['breed'].strip()
        
        if pet_data.get('gender'):
            existing_pet.gender = PetGender(pet_data['gender'])
        
        if 'weight' in pet_data:  # Permitir peso 0 o None
            existing_pet.weight = pet_data['weight']
        
        existing_pet.updated_at = datetime.utcnow()
        
        # Guardar cambios
        return self._pet_repository.update(existing_pet)
    
    def deactivate_pet(self, pet_id: int) -> bool:
        """CASO DE USO: Desactivar mascota (soft delete)"""
        pet = self._pet_repository.find_by_id(pet_id)
        if not pet:
            raise ValueError("Pet not found")
        
        pet.is_active = False
        pet.updated_at = datetime.utcnow()
        self._pet_repository.update(pet)
        
        return True
    
    def search_pets(self, query: str) -> List[Pet]:
        """CASO DE USO: Buscar mascotas por nombre"""
        if not query or len(query.strip()) < 2:
            return []
        
        return self._pet_repository.find_by_name(query.strip())
    
    def get_pet_summary(self, pet_id: int) -> dict:
        """CASO DE USO: Obtener resumen completo de la mascota"""
        pet = self.get_pet_by_id(pet_id)
        if not pet:
            raise ValueError("Pet not found")
        
        # Obtener información del propietario
        client = self._client_repository.find_by_id(pet.client_id)
        
        return {
            'pet': pet,
            'owner': client,
            'age_info': f"{pet.age_in_years} años" if pet.age_in_years else "Edad desconocida",
            'needs_vaccination': pet.needs_vaccination_reminder(),
            'display_info': pet.display_info,
        }
    
    def _validate_pet_data(self, pet_data: dict, is_update: bool = False):
        """Valida los datos de la mascota"""
        # En creación, ciertos campos son obligatorios
        if not is_update:
            if not pet_data.get('name', '').strip():
                raise ValueError("Pet name is required")
            
            if not pet_data.get('client_id'):
                raise ValueError("Client ID is required")
        
        # Validar peso si se proporciona
        if pet_data.get('weight') is not None:
            try:
                weight = float(pet_data['weight'])
                if weight <= 0:
                    raise ValueError("Weight must be positive")
                if weight > 1000:  # 1 tonelada máximo :)
                    raise ValueError("Weight seems unrealistic")
            except (ValueError, TypeError):
                raise ValueError("Weight must be a valid number")
        
        # Validar especies y géneros
        if pet_data.get('species'):
            try:
                PetSpecies(pet_data['species'])
            except ValueError:
                valid_species = [species.value for species in PetSpecies]
                raise ValueError(f"Invalid species. Valid options: {valid_species}")
        
        if pet_data.get('gender'):
            try:
                PetGender(pet_data['gender'])
            except ValueError:
                valid_genders = [gender.value for gender in PetGender]
                raise ValueError(f"Invalid gender. Valid options: {valid_genders}")