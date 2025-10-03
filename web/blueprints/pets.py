"""
EXPLICACIÓN: Blueprint para gestión completa de mascotas (VERSIÓN CORREGIDA).
Simplificado y adaptado al repository SQLPetRepository existente.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date

from infra import get_container
from domain.entities.pet import PetSpecies, PetGender

# Crear blueprint
pets_bp = Blueprint('pets', __name__, template_folder='../templates/pets')

@pets_bp.route('/')
def list_pets():
    """
    RUTA: Lista de todas las mascotas con información del propietario
    """
    try:
        container = get_container()
        pet_service = container.get_pet_service()
        client_service = container.get_client_service()
        
        # Verificar si hay filtros
        search_query = request.args.get('search', '').strip()
        show_inactive = request.args.get('show_inactive', 'false') == 'true'
        
        if search_query:
            pets = pet_service.search_pets(search_query)
            flash(f'Encontradas {len(pets)} mascotas para "{search_query}"', 'info')
        else:
            pets = pet_service.get_all_pets(active_only=not show_inactive)
        
        # Cargar información de propietarios
        pets_with_owners = []
        for pet in pets:
            try:
                owner = client_service.get_client_by_id(pet.client_id)
                pets_with_owners.append({
                    'pet': pet,
                    'owner': owner
                })
            except:
                pets_with_owners.append({
                    'pet': pet,
                    'owner': None
                })
        
        return render_template(
            'pets/list.html', 
            pets_with_owners=pets_with_owners,
            search_query=search_query,
            show_inactive=show_inactive
        )
        
    except Exception as e:
        print(f"Error listando mascotas: {e}")
        flash('Error cargando lista de mascotas.', 'error')
        return render_template('pets/list.html', pets_with_owners=[], search_query='', show_inactive=False)

@pets_bp.route('/create', methods=['GET', 'POST'])
def create_pet():
    """
    RUTA: Crear nueva mascota
    """
    if request.method == 'GET':
        # Obtener mascotas activas para el dropdown (si es necesario)
        container = get_container()
        
        # Obtener veterinarios si es necesario
        user_repo = container.get_user_repository()
        all_users = user_repo.find_all()
        veterinarians = [user for user in all_users if user.role.value in ['veterinarian', 'admin'] and user.is_active]
        
        # Datos pre-seleccionados
        selected_client_id = request.args.get('client_id')
        selected_client = None
        
        if selected_client_id:
            try:
                client_service = container.get_client_service()
                selected_client = client_service.get_client_by_id(int(selected_client_id))
            except:
                pass
        
        return render_template(
            'pets/create.html',
            species=PetSpecies,
            genders=PetGender,
            selected_client=selected_client
        )
    
    try:
        # Obtener y validar datos del formulario
        name = request.form.get('name', '').strip()
        if not name:
            raise ValueError("El nombre de la mascota es obligatorio")
        
        client_id = request.form.get('client_id')
        if not client_id:
            raise ValueError("Debe seleccionar un propietario")
        
        species = request.form.get('species')
        if not species:
            raise ValueError("Debe seleccionar una especie")
        
        gender = request.form.get('gender')
        if not gender:
            raise ValueError("Debe seleccionar el sexo de la mascota")
        
        # Procesar peso
        weight = None
        if request.form.get('weight'):
            try:
                weight = float(request.form.get('weight'))
                if weight <= 0:
                    raise ValueError("El peso debe ser mayor a 0")
            except ValueError:
                raise ValueError("El peso debe ser un número válido")
        
        # Preparar datos
        pet_data = {
            'name': name,
            'species': species,
            'breed': request.form.get('breed', '').strip() or None,
            'birth_date': request.form.get('birth_date') or None,
            'gender': gender,
            'color': request.form.get('color', '').strip() or None,
            'weight': weight,
            'microchip_number': request.form.get('microchip_number', '').strip() or None,
            'client_id': int(client_id)
        }
        
        # Crear mascota
        container = get_container()
        pet_service = container.get_pet_service()
        
        new_pet = pet_service.create_pet(pet_data)
        
        flash(f'Mascota {new_pet.name} registrada exitosamente.', 'success')
        return redirect(url_for('pets.view_pet', pet_id=new_pet.id))
        
    except ValueError as e:
        flash(str(e), 'error')
        # Recargar formulario manteniendo datos
        return render_template(
            'pets/create.html',
            species=PetSpecies,
            genders=PetGender,
            **request.form.to_dict()
        )
    
    except Exception as e:
        print(f"Error creando mascota: {e}")
        flash('Error registrando mascota. Intente nuevamente.', 'error')
        return redirect(url_for('pets.create_pet'))

@pets_bp.route('/<int:pet_id>')
def view_pet(pet_id):
    """
    RUTA: Ver detalles de una mascota específica
    """
    try:
        container = get_container()
        pet_service = container.get_pet_service()
        
        # Obtener resumen completo de la mascota
        pet_summary = pet_service.get_pet_summary(pet_id)
        
        if not pet_summary:
            flash('Mascota no encontrada.', 'error')
            return redirect(url_for('pets.list_pets'))
        
        # Obtener historial de citas si existe el service
        try:
            appointment_service = container.get_appointment_service()
            appointments = appointment_service.get_appointments_by_pet(pet_id)
            recent_appointments = sorted(appointments, key=lambda x: x.appointment_date, reverse=True)[:5]
        except:
            recent_appointments = []
        
        return render_template(
            'pets/view.html',
            pet_summary=pet_summary,
            recent_appointments=recent_appointments
        )
        
    except Exception as e:
        print(f"Error viendo mascota: {e}")
        flash('Error cargando información de la mascota.', 'error')
        return redirect(url_for('pets.list_pets'))

@pets_bp.route('/<int:pet_id>/edit', methods=['GET', 'POST'])
def edit_pet(pet_id):
    """
    RUTA: Editar mascota existente - VERSIÓN SIMPLIFICADA
    """
    try:
        container = get_container()
        pet_service = container.get_pet_service()
        
        # Obtener mascota existente
        pet = pet_service.get_pet_by_id(pet_id)
        if not pet:
            flash('Mascota no encontrada.', 'error')
            return redirect(url_for('pets.list_pets'))
        
    except Exception as e:
        flash('Error cargando mascota.', 'error')
        return redirect(url_for('pets.list_pets'))

    if request.method == 'GET':
        return render_template(
            'pets/edit.html',
            pet=pet,
            species=PetSpecies,
            genders=PetGender
        )

    # Procesar actualización
    try:
        # Validar campos básicos
        name = request.form.get('name', '').strip()
        if not name:
            raise ValueError("El nombre de la mascota es obligatorio")
        
        species = request.form.get('species')
        if not species:
            raise ValueError("Debe seleccionar una especie")
        
        gender = request.form.get('gender')
        if not gender:
            raise ValueError("Debe seleccionar el sexo de la mascota")
        
        # Procesar peso
        weight = None
        if request.form.get('weight'):
            try:
                weight = float(request.form.get('weight'))
                if weight <= 0:
                    raise ValueError("El peso debe ser mayor a 0")
            except ValueError:
                raise ValueError("El peso debe ser un número válido")
        
        # Preparar datos de actualización
        pet_data = {
            'name': name,
            'species': species,
            'breed': request.form.get('breed', '').strip() or None,
            'birth_date': request.form.get('birth_date') or None,
            'gender': gender,
            'color': request.form.get('color', '').strip() or None,
            'weight': weight,
            'microchip_number': request.form.get('microchip_number', '').strip() or None
        }
        
        # Actualizar mascota
        updated_pet = pet_service.update_pet(pet_id, pet_data)
        
        flash(f'Mascota {updated_pet.name} actualizada exitosamente.', 'success')
        return redirect(url_for('pets.view_pet', pet_id=pet_id))
        
    except ValueError as e:
        flash(str(e), 'error')
        return render_template('pets/edit.html', pet=pet, species=PetSpecies, genders=PetGender)

    except Exception as e:
        print(f"Error actualizando mascota: {e}")
        flash('Error actualizando mascota. Intente nuevamente.', 'error')
        return render_template('pets/edit.html', pet=pet, species=PetSpecies, genders=PetGender)
    
@pets_bp.route('/<int:pet_id>/toggle-status', methods=['POST'])
def toggle_pet_status(pet_id):
    """
    RUTA: Activar/Desactivar mascota
    """
    try:
        container = get_container()
        pet_service = container.get_pet_service()
        
        pet = pet_service.get_pet_by_id(pet_id)
        if not pet:
            flash('Mascota no encontrada.', 'error')
            return redirect(url_for('pets.list_pets'))
        
        # Cambiar estado
        if pet.is_active:
            # Desactivar mascota
            pet_service.deactivate_pet(pet_id)
            flash(f'Mascota {pet.name} desactivada exitosamente.', 'success')
        else:
            # Activar mascota usando update_pet
            pet_service.update_pet(pet_id, {'is_active': True})
            flash(f'Mascota {pet.name} activada exitosamente.', 'success')
        
        return redirect(url_for('pets.edit_pet', pet_id=pet_id))
        
    except Exception as e:
        print(f"Error cambiando estado de mascota: {e}")
        flash('Error cambiando estado de mascota.', 'error')
        return redirect(url_for('pets.edit_pet', pet_id=pet_id))

@pets_bp.route('/by-client/<int:client_id>')
def pets_by_client(client_id):
    """
    RUTA: Mascotas de un cliente específico
    """
    try:
        container = get_container()
        pet_service = container.get_pet_service()
        client_service = container.get_client_service()
        
        # Verificar que el cliente existe
        client = client_service.get_client_by_id(client_id)
        if not client:
            flash('Cliente no encontrado.', 'error')
            return redirect(url_for('clients.list_clients'))
        
        # Obtener mascotas del cliente
        pets = pet_service.get_pets_by_client(client_id)
        
        return render_template(
            'pets/by_client.html',
            pets=pets,
            client=client
        )
        
    except Exception as e:
        print(f"Error obteniendo mascotas del cliente: {e}")
        flash('Error cargando mascotas del cliente.', 'error')
        return redirect(url_for('clients.list_clients'))

@pets_bp.route('/search')
def search_pets():
    """
    RUTA: Búsqueda AJAX de mascotas
    """
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([])
        
        container = get_container()
        pet_service = container.get_pet_service()
        client_service = container.get_client_service()
        
        pets = pet_service.search_pets(query)
        
        # Formatear para JSON
        results = []
        for pet in pets[:10]:  # Máximo 10 resultados
            try:
                owner = client_service.get_client_by_id(pet.client_id)
                owner_name = owner.full_name if owner else "Propietario desconocido"
            except:
                owner_name = "Propietario desconocido"
            
            results.append({
                'id': pet.id,
                'name': pet.name,
                'species': pet.species.value.title(),
                'owner': owner_name,
                'display': f"{pet.name} ({pet.species.value.title()}) - {owner_name}"
            })
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error en búsqueda de mascotas: {e}")
        return jsonify([])