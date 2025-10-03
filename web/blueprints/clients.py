"""
EXPLICACIÓN: Blueprint para gestión completa de clientes (propietarios).
Implementa CRUD completo con validaciones y búsquedas.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

from domain.entities import pet
from infra import get_container

# Crear blueprint
clients_bp = Blueprint('clients', __name__, template_folder='../templates/clients')

@clients_bp.route('/')
def list_clients():
    """
    RUTA: Lista de todos los clientes
    Incluye búsqueda en tiempo real
    """
    try:
        container = get_container()
        client_service = container.get_client_service()
        
        # Verificar si hay término de búsqueda
        search_query = request.args.get('search', '').strip()
        
        if search_query:
            clients = client_service.search_clients(search_query)
            flash(f'Encontrados {len(clients)} clientes para "{search_query}"', 'info')
        else:
            clients = client_service.get_all_clients()
        
        return render_template('clients/list.html', clients=clients, search_query=search_query)
        
    except Exception as e:
        print(f"Error listando clientes: {e}")
        flash('Error cargando lista de clientes.', 'error')
        return render_template('clients/list.html', clients=[], search_query='')

@clients_bp.route('/create', methods=['GET', 'POST'])
def create_client():
    """
    RUTA: Crear nuevo cliente
    GET: Muestra formulario
    POST: Procesa creación
    """
    if request.method == 'GET':
        return render_template('clients/create.html')
    
    try:
        # Obtener datos del formulario
        client_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'email': request.form.get('email', '').strip().lower(),
            'phone': request.form.get('phone', '').strip(),
            'address': request.form.get('address', '').strip(),
            'identification_number': request.form.get('identification_number', '').strip()
        }
        
        # Limpiar campos vacíos
        for key, value in client_data.items():
            if value == '':
                client_data[key] = None
        
        # Crear cliente usando el service
        container = get_container()
        client_service = container.get_client_service()
        
        new_client = client_service.create_client(client_data)
        
        flash(f'Cliente {new_client.full_name} creado exitosamente.', 'success')
        return redirect(url_for('clients.view_client', client_id=new_client.id))
        
    except ValueError as e:
        flash(str(e), 'error')
        return render_template('clients/create.html', **client_data)
    
    except Exception as e:
        print(f"Error creando cliente: {e}")
        flash('Error creando cliente. Intenta nuevamente.', 'error')
        return render_template('clients/create.html', **client_data)

@clients_bp.route('/<int:client_id>')
def view_client(client_id):
    """
    RUTA: Ver detalles de un cliente específico
    Incluye sus mascotas y citas recientes
    """
    try:
        container = get_container()
        client_service = container.get_client_service()
        pet_service = container.get_pet_service()
        
        # Obtener cliente
        client = client_service.get_client_by_id(client_id)
        if not client:
            flash('Cliente no encontrado.', 'error')
            return redirect(url_for('clients.list_clients'))
        
        # Obtener mascotas del cliente
        pets = pet_service.get_pets_by_client(client_id)
        
        # Obtener resumen del cliente
        client_summary = client_service.get_client_summary(client_id)
        
        return render_template(
            'clients/view.html', 
            client=client, 
            pets=pets,
            client_summary=client_summary
        )
        
    except Exception as e:
        print(f"Error viendo cliente: {e}")
        flash('Error cargando información del cliente.', 'error')
        return redirect(url_for('clients.list_clients'))

@clients_bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
def edit_client(client_id):
    """
    RUTA: Editar cliente existente
    GET: Muestra formulario con datos actuales
    POST: Procesa actualización
    """
    try:
        container = get_container()
        client_service = container.get_client_service()
    
        # Obtener cliente existente
        client = client_service.get_client_by_id(client_id)
        if not client:
            flash('Cliente no encontrado.', 'error')
            return redirect(url_for('clients.list_clients'))
           
    except Exception as e:
        flash('Error cargando cliente.', 'error')
        return redirect(url_for('clients.list_clients'))

    if request.method == 'GET':
        return render_template('clients/edit.html', client=client)

    try:
        # Obtener datos del formulario
        client_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'email': request.form.get('email', '').strip().lower() or None,
            'phone': request.form.get('phone', '').strip() or None,
            'address': request.form.get('address', '').strip() or None,
            'identification_number': request.form.get('identification_number', '').strip() or None
        }
        
        # Actualizar cliente usando el service
        updated_client = client_service.update_client(client_id, client_data)
        
        flash(f'Cliente {updated_client.full_name} actualizado exitosamente.', 'success')
        return redirect(url_for('clients.view_client', client_id=client_id))
        
    except ValueError as e:
        flash(str(e), 'error')
        return render_template('clients/edit.html', client=client)

    except Exception as e:
        print(f"Error actualizando cliente: {e}")
        flash('Error actualizando cliente.', 'error')
        return render_template('clients/edit.html', client=client)
    
@clients_bp.route('/<int:client_id>/delete', methods=['POST'])
def delete_client(client_id):
    """
    RUTA: Eliminar cliente
    Solo vía POST para evitar eliminaciones accidentales
    """
    try:
        container = get_container()
        client_service = container.get_client_service()
        pet_service = container.get_pet_service()
        
        # Verificar si el cliente existe
        client = client_service.get_client_by_id(client_id)
        if not client:
            flash('Cliente no encontrado.', 'error')
            return redirect(url_for('clients.list_clients'))
        
        # Verificar que no tenga mascotas activas
        pets = pet_service.get_pets_by_client(client_id)
        active_pets = [pet for pet in pets if pet.is_active]
        if active_pets:
            flash(f'No se puede eliminar el cliente porque tiene {len(active_pets)} mascota(s) activa(s).', 'error')
            return redirect(url_for('clients.view_client', client_id=client_id))

        # Proceder a eliminar cliente
        client_name = client.full_name
        success = client_service.delete_client(client_id)
        if success:
            flash(f'Cliente {client_name} eliminado exitosamente.', 'success')
        else:
            flash('Error eliminando cliente.', 'error')
        return redirect(url_for('clients.list_clients'))
    except Exception as e:
        print(f"Error eliminando cliente: {e}")
        flash('Error eliminando cliente.', 'error')
        return redirect(url_for('clients.list_client'))
    
@clients_bp.route('/search')
def search_clients():
    """
    RUTA: Búsqueda avanzada de clientes (para AJAX)
    Retorna JSON con resultados
    """
    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([])  # Evitar búsquedas muy cortas
        container = get_container()
        client_service = container.get_client_service()
        clients = client_service.search_clients(query)
        # Formatear para JSON
        results = []
        for client in clients[:10]:  # Máximo 10 resultados
            results.append({
                'id': client.id,
                'name': client.full_name,
                'email': client.email,
                'phone': client.phone,
                'display': f"{client.full_name} - {client.display_contact}"
            })
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error en búsqueda de clientes: {e}")
        return jsonify([])