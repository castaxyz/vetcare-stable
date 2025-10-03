"""
EXPLICACIÓN: Archivo principal para ejecutar la aplicación Flask.
Punto de entrada que inicializa todo el sistema y crea usuarios por defecto.
"""

import os
from datetime import datetime
from web.app import create_app
from infra import get_container
from domain.entities.user import UserRole

def create_default_users():
    """
    Crea usuarios por defecto para desarrollo y demo.
    Solo se ejecuta si no existen usuarios en el sistema.
    """
    try:
        container = get_container()
        user_repo = container.get_user_repository()
        auth_service = container.get_auth_service()
        
        # Verificar si ya existen usuarios
        existing_users = user_repo.find_all()
        if existing_users:
            print(f"✅ Sistema ya tiene {len(existing_users)} usuarios registrados")
            return
        
        # Crear usuarios por defecto
        default_users = [
            {
                'username': 'admin',
                'email': 'admin@vetcare.com',
                'password': 'admin123',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'role': 'admin'
            },
            {
                'username': 'vet',
                'email': 'vet@vetcare.com', 
                'password': 'vet123',
                'first_name': 'Dr. María',
                'last_name': 'González',
                'role': 'veterinarian'
            },
            {
                'username': 'recep',
                'email': 'recep@vetcare.com',
                'password': 'recep123', 
                'first_name': 'Ana',
                'last_name': 'Martínez',
                'role': 'receptionist'
            }
        ]
        
        created_count = 0
        for user_data in default_users:
            try:
                auth_service.register_user(user_data, created_by_admin=True)
                created_count += 1
                print(f"✅ Usuario creado: {user_data['username']} ({user_data['role']})")
            except Exception as e:
                print(f"❌ Error creando usuario {user_data['username']}: {e}")
        
        print(f"🎉 {created_count} usuarios por defecto creados exitosamente")
        
    except Exception as e:
        print(f"❌ Error creando usuarios por defecto: {e}")

def create_sample_data():
    """
    Crea datos de ejemplo para desarrollo (clientes y mascotas).
    Solo para ambiente de desarrollo.
    """
    try:
        # Solo en desarrollo
        if os.environ.get('FLASK_CONFIG', 'development') != 'development':
            return
            
        container = get_container()
        client_service = container.get_client_service()
        pet_service = container.get_pet_service()
        
        # Verificar si ya hay datos
        existing_clients = client_service.get_all_clients()
        if existing_clients:
            print(f"✅ Sistema ya tiene {len(existing_clients)} clientes")
            return
        
        # Datos de ejemplo
        sample_clients = [
            {
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'email': 'juan.perez@email.com',
                'phone': '555-0101',
                'address': 'Calle Principal 123',
                'identification_number': '12345678'
            },
            {
                'first_name': 'María',
                'last_name': 'García',
                'email': 'maria.garcia@email.com', 
                'phone': '555-0102',
                'address': 'Avenida Central 456'
            },
            {
                'first_name': 'Carlos',
                'last_name': 'López',
                'phone': '555-0103',
                'address': 'Plaza Mayor 789'
            }
        ]
        
        created_clients = []
        for client_data in sample_clients:
            try:
                client = client_service.create_client(client_data)
                created_clients.append(client)
                print(f"✅ Cliente creado: {client.full_name}")
            except Exception as e:
                print(f"❌ Error creando cliente: {e}")
        
        # Crear mascotas de ejemplo
        sample_pets = [
            {
                'name': 'Max',
                'species': 'dog',
                'breed': 'Labrador',
                'gender': 'male',
                'birth_date': '2020-03-15',
                'color': 'Dorado',
                'weight': 25.5,
                'client_id': created_clients[0].id if created_clients else 1
            },
            {
                'name': 'Luna',
                'species': 'cat', 
                'breed': 'Persa',
                'gender': 'female',
                'birth_date': '2021-07-20',
                'color': 'Blanco',
                'weight': 4.2,
                'client_id': created_clients[1].id if len(created_clients) > 1 else 1
            },
            {
                'name': 'Rocky',
                'species': 'dog',
                'breed': 'Pastor Alemán', 
                'gender': 'male',
                'color': 'Negro y café',
                'weight': 30.0,
                'client_id': created_clients[2].id if len(created_clients) > 2 else 1
            }
        ]
        
        created_pets = 0
        for pet_data in sample_pets:
            try:
                pet = pet_service.create_pet(pet_data)
                created_pets += 1
                print(f"✅ Mascota creada: {pet.name} ({pet.species.value})")
            except Exception as e:
                print(f"❌ Error creando mascota: {e}")
        
        print(f"🎉 Datos de ejemplo creados: {len(created_clients)} clientes, {created_pets} mascotas")
        
    except Exception as e:
        print(f"❌ Error creando datos de ejemplo: {e}")

def main():
    """
    Función principal que inicializa y ejecuta la aplicación.
    """
    print("🚀 Iniciando VetCare...")
    print("=" * 50)
    
    # Obtener configuración del entorno
    config_name = os.environ.get('FLASK_CONFIG', 'development')
    print(f"📝 Configuración: {config_name}")
    
    # Crear aplicación Flask
    app = create_app(config_name)
    
    # Configuraciones adicionales según el entorno
    if config_name == 'development':
        print("🛠️  Modo desarrollo activado")
        
        # Crear usuarios por defecto
        with app.app_context():
            create_default_users()
            create_sample_data()
    
    # Información de inicio
    print("=" * 50)
    print("🏥 VetCare - Sistema de Gestión Veterinaria")
    print(f"🌐 Servidor: http://127.0.0.1:5000")
    print(f"👤 Usuario admin: admin / admin123")
    print(f"👨‍⚕️ Usuario vet: vet / vet123") 
    print(f"👩‍💼 Usuario recep: recep / recep123")
    print("=" * 50)
    
    # Ejecutar aplicación
    try:
        app.run(
            host='0.0.0.0' if config_name == 'production' else '127.0.0.1',
            port=int(os.environ.get('PORT', 5000)),
            debug=(config_name == 'development')
        )
    except KeyboardInterrupt:
        print("\n👋 Cerrando VetCare...")
    except Exception as e:
        print(f"❌ Error ejecutando aplicación: {e}")

if __name__ == '__main__':
    main()