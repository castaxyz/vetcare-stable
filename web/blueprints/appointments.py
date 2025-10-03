"""
EXPLICACIÓN: Blueprint para gestión completa de citas veterinarias.
Sistema más complejo que incluye programación, estados y disponibilidad.
"""

import calendar
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, date, timedelta
import json

from infra import get_container
from domain.entities.appointment import AppointmentType, AppointmentStatus

# Crear blueprint
appointments_bp = Blueprint('appointments', __name__, template_folder='../templates/appointments')

@appointments_bp.route('/')
def list_appointments():
    """
    RUTA: Lista de citas con filtros - VERSIÓN ACTUALIZADA
    """
    try:
        container = get_container()
        appointment_service = container.get_appointment_service()
        
        # Obtener parámetros de filtro
        date_filter = request.args.get('date')
        status_filter = request.args.get('status')
        
        # Fecha por defecto: hoy
        if not date_filter:
            date_filter = date.today().strftime('%Y-%m-%d')
        
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            filter_date = date.today()
            date_filter = filter_date.strftime('%Y-%m-%d')
        
        # Calcular fechas para navegación
        prev_date = (filter_date - timedelta(days=1)).strftime('%Y-%m-%d')
        next_date = (filter_date + timedelta(days=1)).strftime('%Y-%m-%d')
        today_str = date.today().strftime('%Y-%m-%d')
        tomorrow_str = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        is_today = filter_date == date.today()
        
        # Obtener citas (SIN validación de fecha pasada para consulta)
        if status_filter and status_filter != 'all':
            try:
                status_enum = AppointmentStatus(status_filter)
                appointments = appointment_service.get_all_appointments(status_filter=status_enum)
                # Filtrar por fecha
                if date_filter != date.today().strftime('%Y-%m-%d'):  # Solo filtrar si no es hoy
                    appointments = [apt for apt in appointments 
                        if apt.appointment_date.date() == filter_date]
            except ValueError:
                appointments = appointment_service.get_appointments_by_date(filter_date)
        else:
            appointments = appointment_service.get_appointments_by_date(filter_date)
        
        # Obtener información completa para cada cita
        appointments_with_info = []
        for appointment in appointments:
            try:
                pet_service = container.get_pet_service()
                client_service = container.get_client_service()
                user_repo = container.get_user_repository()
                
                pet = pet_service.get_pet_by_id(appointment.pet_id)
                client = None
                veterinarian = None
                
                if pet:
                    client = client_service.get_client_by_id(pet.client_id)
                
                if appointment.veterinarian_id:
                    veterinarian = user_repo.find_by_id(appointment.veterinarian_id)
                
                appointments_with_info.append({
                    'appointment': appointment,
                    'pet': pet,
                    'client': client,
                    'veterinarian': veterinarian
                })
            except Exception as e:
                print(f"Error procesando cita {appointment.id}: {e}")
                continue
        
        # Ordenar por hora
        appointments_with_info.sort(key=lambda x: x['appointment'].appointment_date)
        
        return render_template(
            'appointments/list.html',
            appointments_with_info=appointments_with_info,
            date_filter=date_filter,
            status_filter=status_filter,
            appointment_statuses=AppointmentStatus,
            filter_date_obj=filter_date,
            prev_date=prev_date,
            next_date=next_date,
            today_str=today_str,
            tomorrow_str=tomorrow_str,
            is_today=is_today
        )
        
    except Exception as e:
        print(f"Error listando citas: {e}")
        flash('Error cargando lista de citas.', 'error')
        return render_template(
            'appointments/list.html',
            appointments_with_info=[],
            date_filter=date.today().strftime('%Y-%m-%d'),
            status_filter='all',
            appointment_statuses=AppointmentStatus,
            filter_date_obj=date.today(),
            prev_date=(date.today() - timedelta(days=1)).strftime('%Y-%m-%d'),
            next_date=(date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            today_str=date.today().strftime('%Y-%m-%d'),
            tomorrow_str=(date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            is_today=True
        )

@appointments_bp.route('/create', methods=['GET', 'POST'])
def create_appointment():
    """
    RUTA: Crear nueva cita
    """
    if request.method == 'GET':
        # Obtener listas para dropdowns
        container = get_container()
        
        # Obtener mascotas activas
        pet_service = container.get_pet_service()
        pets = pet_service.get_all_pets(active_only=True)
        
        # Obtener veterinarios
        user_repo = container.get_user_repository()
        all_users = user_repo.find_all()
        veterinarians = [user for user in all_users if user.role.value in ['veterinarian', 'admin'] and user.is_active]
        
        # Datos pre-seleccionados si vienen como parámetros
        selected_pet_id = request.args.get('pet_id')
        selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
        
        return render_template(
            'appointments/create.html',
            pets=pets,
            veterinarians=veterinarians,
            appointment_types=AppointmentType,
            selected_pet_id=selected_pet_id,
            selected_date=selected_date
        )
    
    try:
        # Obtener datos del formulario
        appointment_data = {
            'pet_id': int(request.form.get('pet_id')),
            'veterinarian_id': int(request.form.get('veterinarian_id')) if request.form.get('veterinarian_id') else None,
            'appointment_date': request.form.get('appointment_date'),
            'appointment_time': request.form.get('appointment_time'),
            'appointment_type': request.form.get('appointment_type'),
            'duration_minutes': int(request.form.get('duration_minutes', 30)),
            'reason': request.form.get('reason', '').strip() or None,
            'notes': request.form.get('notes', '').strip() or None,
            'created_by': session.get('user_id')
        }
        
        # Combinar fecha y hora
        date_str = appointment_data['appointment_date']
        time_str = appointment_data['appointment_time']
        datetime_str = f"{date_str} {time_str}"
        appointment_data['appointment_date'] = datetime_str
        
        # Eliminar campos que no necesita el service
        del appointment_data['appointment_time']
        
        # Crear cita usando el service
        container = get_container()
        appointment_service = container.get_appointment_service()
        
        new_appointment = appointment_service.schedule_appointment(appointment_data)
        
        flash('Cita programada exitosamente.', 'success')
        return redirect(url_for('appointments.view_appointment', appointment_id=new_appointment.id))
        
    except ValueError as e:
        flash(str(e), 'error')
        # Recargar formulario con datos
        container = get_container()
        pet_service = container.get_pet_service()
        pets = pet_service.get_all_pets(active_only=True)
        
        user_repo = container.get_user_repository()
        all_users = user_repo.find_all()
        veterinarians = [user for user in all_users if user.role.value in ['veterinarian', 'admin']]
        
        return render_template(
            'appointments/create.html',
            pets=pets,
            veterinarians=veterinarians,
            appointment_types=AppointmentType,
            **appointment_data
        )
    
    except Exception as e:
        print(f"Error creando cita: {e}")
        flash('Error programando cita.', 'error')
        return redirect(url_for('appointments.list_appointments'))

@appointments_bp.route('/<int:appointment_id>')
def view_appointment(appointment_id):
    """
    RUTA: Ver detalles de una cita específica
    """
    try:
        container = get_container()
        appointment_service = container.get_appointment_service()
        
        # Obtener cita
        appointment = appointment_service.get_appointment_by_id(appointment_id)
        if not appointment:
            flash('Cita no encontrada.', 'error')
            return redirect(url_for('appointments.list_appointments'))
        
        # Obtener información relacionada
        pet_service = container.get_pet_service()
        client_service = container.get_client_service()
        user_repo = container.get_user_repository()
        
        pet = pet_service.get_pet_by_id(appointment.pet_id)
        client = None
        veterinarian = None
        creator = None
        
        if pet:
            client = client_service.get_client_by_id(pet.client_id)
        
        if appointment.veterinarian_id:
            veterinarian = user_repo.find_by_id(appointment.veterinarian_id)
        
        if appointment.created_by:
            creator = user_repo.find_by_id(appointment.created_by)
        
        return render_template(
            'appointments/view.html',
            appointment=appointment,
            pet=pet,
            client=client,
            veterinarian=veterinarian,
            creator=creator
        )
        
    except Exception as e:
        print(f"Error viendo cita: {e}")
        flash('Error cargando información de la cita.', 'error')
        return redirect(url_for('appointments.list_appointments'))

@appointments_bp.route('/<int:appointment_id>/confirm', methods=['POST'])
def confirm_appointment(appointment_id):
    """RUTA: Confirmar cita programada"""
    try:
        container = get_container()
        appointment_service = container.get_appointment_service()
        
        appointment_service.confirm_appointment(appointment_id)
        flash('Cita confirmada exitosamente.', 'success')
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        print(f"Error confirmando cita: {e}")
        flash('Error confirmando cita.', 'error')
    
    # CAMBIO: Redirigir de vuelta a edit en lugar de lista
    return redirect(url_for('appointments.edit_appointment', appointment_id=appointment_id))

@appointments_bp.route('/<int:appointment_id>/complete', methods=['POST'])
def complete_appointment(appointment_id):
    """RUTA: Completar cita"""
    try:
        completion_notes = request.form.get('completion_notes', '').strip()
        
        container = get_container()
        appointment_service = container.get_appointment_service()
        
        appointment_service.complete_appointment(appointment_id, completion_notes)
        flash('Cita completada exitosamente.', 'success')
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        print(f"Error completando cita: {e}")
        flash('Error completando cita.', 'error')
    
    # CAMBIO: Redirigir de vuelta a edit en lugar de lista
    return redirect(url_for('appointments.edit_appointment', appointment_id=appointment_id))

@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
def cancel_appointment(appointment_id):
    """RUTA: Cancelar cita"""
    try:
        cancellation_reason = request.form.get('cancellation_reason', '').strip()
        
        container = get_container()
        appointment_service = container.get_appointment_service()
        
        appointment_service.cancel_appointment(appointment_id, cancellation_reason)
        flash('Cita cancelada exitosamente.', 'success')
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        print(f"Error cancelando cita: {e}")
        flash('Error cancelando cita.', 'error')
    
    # CAMBIO: Redirigir de vuelta a edit en lugar de lista  
    return redirect(url_for('appointments.edit_appointment', appointment_id=appointment_id))

@appointments_bp.route('/calendar')
def calendar_view():
    """
    RUTA: Vista de calendario de citas
    """
    try:
        container = get_container()
        appointment_service = container.get_appointment_service()
        
        # Obtener citas del mes actual
        today = date.today()
        start_of_month = today.replace(day=1)
        
        # Calcular fin del mes
        if start_of_month.month == 12:
            end_of_month = start_of_month.replace(year=start_of_month.year + 1, month=1) - timedelta(days=1)
        else:
            end_of_month = start_of_month.replace(month=start_of_month.month + 1) - timedelta(days=1)
        
        start_datetime = datetime.combine(start_of_month, datetime.min.time())
        end_datetime = datetime.combine(end_of_month, datetime.max.time())
        
        appointments = appointment_service.find_by_date_range(start_datetime, end_datetime)
        
        # Formatear para el calendario
        calendar_events = []
        for appointment in appointments:
            try:
                pet_service = container.get_pet_service()
                pet = pet_service.get_pet_by_id(appointment.pet_id)
                
                event_title = f"{appointment.appointment_date.strftime('%H:%M')} - {pet.name if pet else 'Mascota desconocida'}"
                
                calendar_events.append({
                    'id': appointment.id,
                    'title': event_title,
                    'start': appointment.appointment_date.isoformat(),
                    'end': appointment.end_time.isoformat(),
                    'color': get_status_color(appointment.status),
                    'url': url_for('appointments.view_appointment', appointment_id=appointment.id)
                })
            except Exception as e:
                print(f"Error procesando cita para calendario: {e}")
                continue
        
        return render_template(
            'appointments/calendar.html',
            calendar_events=calendar_events,
            current_month=today.strftime('%Y-%m')
        )
        
    except Exception as e:
        print(f"Error en vista de calendario: {e}")
        flash('Error cargando calendario.', 'error')
        return render_template('appointments/calendar.html', calendar_events=[])

@appointments_bp.route('/availability/<int:vet_id>/<date>')
def check_availability(vet_id, date):
    """
    RUTA: Verificar disponibilidad de veterinario (AJAX)
    """
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        container = get_container()
        appointment_service = container.get_appointment_service()
        
        available_slots = appointment_service.get_availability_slots(
            date_target=target_date,
            veterinarian_id=vet_id,
            duration_minutes=30
        )
        
        return jsonify([
            {
                'time': slot['start_time'].strftime('%H:%M'),
                'display': slot['display_time']
            } for slot in available_slots
        ])
        
    except Exception as e:
        print(f"Error verificando disponibilidad: {e}")
        return jsonify([])

def get_status_color(status: AppointmentStatus) -> str:
    """Helper function para obtener colores según el estado"""
    color_map = {
        AppointmentStatus.SCHEDULED: '#6c757d',  # Gris
        AppointmentStatus.CONFIRMED: '#17a2b8',  # Azul
        AppointmentStatus.IN_PROGRESS: '#ffc107', # Amarillo
        AppointmentStatus.COMPLETED: '#28a745',   # Verde
        AppointmentStatus.CANCELLED: '#dc3545',   # Rojo
        AppointmentStatus.NO_SHOW: '#fd7e14'      # Naranja
    }
    return color_map.get(status, '#6c757d')


@appointments_bp.route('/<int:appointment_id>/edit', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    """
    RUTA: Ver y editar detalles de una cita específica
    GET: Muestra formulario con datos actuales
    POST: Procesa actualización
    """
    try:
        container = get_container()
        appointment_service = container.get_appointment_service()
        
        # Obtener cita
        appointment = appointment_service.get_appointment_by_id(appointment_id)
        if not appointment:
            flash('Cita no encontrada.', 'error')
            return redirect(url_for('appointments.list_appointments'))
        
        # Obtener información relacionada
        pet_service = container.get_pet_service()
        client_service = container.get_client_service()
        user_repo = container.get_user_repository()
        
        pet = pet_service.get_pet_by_id(appointment.pet_id)
        client = None
        veterinarian = None
        creator = None

        # En el método edit_appointment, después de obtener el pet:
        if pet and pet.birth_date:
            from datetime import date
            today = date.today()
            age = today.year - pet.birth_date.year - ((today.month, today.day) < (pet.birth_date.month, pet.birth_date.day))
            pet.calculated_age = age  # Agregar como atributo temporal
        
        if pet:
            client = client_service.get_client_by_id(pet.client_id)
        
        if appointment.veterinarian_id:
            veterinarian = user_repo.find_by_id(appointment.veterinarian_id)
        
        if appointment.created_by:
            creator = user_repo.find_by_id(appointment.created_by)
        
        if request.method == 'GET':
            # Obtener tipos de cita para el dropdown
            from domain.entities.appointment import AppointmentType
            
            return render_template(
                'appointments/edit.html',
                appointment=appointment,
                pet=pet,
                client=client,
                veterinarian=veterinarian,
                creator=creator,
                appointment_types=AppointmentType
            )
        
       # POST - Procesar actualización
        try:
            # Obtener datos del formulario
            date_str = request.form.get('appointment_date')
            time_str = request.form.get('appointment_time')
            
            # Validar datos requeridos
            if not date_str or not time_str:
                raise ValueError("Date and time are required")
            
            # Combinar fecha y hora
            datetime_str = f"{date_str} {time_str}"
            appointment_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
            
            # Datos actualizados
            update_data = {
                'appointment_date': appointment_datetime,
                'duration_minutes': int(request.form.get('duration_minutes', 30)),
                'appointment_type': request.form.get('appointment_type'),
                'reason': request.form.get('reason', '').strip() or None,
                'notes': request.form.get('notes', '').strip() or None
            }
            
            print(f"Updating appointment {appointment_id} with data: {update_data}")  # Debug
            
            # Actualizar cita usando el service
            updated_appointment = appointment_service.update_appointment(appointment_id, update_data)
            
            flash('Cita actualizada exitosamente.', 'success')
            return redirect(url_for('appointments.edit_appointment', appointment_id=appointment_id))
            
        except ValueError as e:
            print(f"ValueError in edit_appointment: {e}")  # Debug
            flash(str(e), 'error')
        except Exception as e:
            print(f"Exception in edit_appointment: {e}")  # Debug
            flash('Error actualizando la cita.', 'error')

        # En caso de error, recargar la página con los tipos de cita
        from domain.entities.appointment import AppointmentType
        return render_template(
            'appointments/edit.html',
            appointment=appointment,
            pet=pet,
            client=client,
            veterinarian=veterinarian,
            creator=creator,
            appointment_types=AppointmentType
        )
        
    except Exception as e:
        print(f"Error en edit_appointment: {e}")
        flash('Error cargando información de la cita.', 'error')
        return redirect(url_for('appointments.list_appointments'))

@appointments_bp.route('/<int:appointment_id>/start', methods=['POST'])
def start_appointment(appointment_id):
    """RUTA: Iniciar atención de cita (cambiar a 'in_progress')"""
    try:
        container = get_container()
        appointment_service = container.get_appointment_service()
        
        # Obtener la cita
        appointment = appointment_service.get_appointment_by_id(appointment_id)
        if not appointment:
            flash('Cita no encontrada.', 'error')
            return redirect(url_for('appointments.edit_appointment', appointment_id=appointment_id))
        
        # Verificar que esté en estado confirmado
        if appointment.status.value != 'confirmed':
            flash('Solo se pueden iniciar citas confirmadas.', 'error')
            return redirect(url_for('appointments.edit_appointment', appointment_id=appointment_id))
        
        # Cambiar estado a 'in_progress'
        appointment_service.start_appointment(appointment_id)
        
        flash('Atención iniciada exitosamente.', 'success')
        return redirect(url_for('appointments.edit_appointment', appointment_id=appointment_id))
        
    except ValueError as e:
        flash(str(e), 'error')
    except Exception as e:
        print(f"Error iniciando cita: {e}")
        flash('Error iniciando atención.', 'error')
    
    return redirect(url_for('appointments.edit_appointment', appointment_id=appointment_id))