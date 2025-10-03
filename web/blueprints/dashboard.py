"""
EXPLICACIÓN: Blueprint del dashboard principal que muestra resumen de la clínica.
Es la página de inicio después del login con estadísticas y accesos rápidos.
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from datetime import datetime, date, timedelta
from sqlalchemy.exc import SQLAlchemyError

from infra import get_container
from domain.entities.appointment import AppointmentStatus

# Crear blueprint
dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates/dashboard')

@dashboard_bp.route('/')
def index():
    """
    RUTA: Dashboard principal - versión segura
    """
    try:
        container = get_container()
        
        # Intentar obtener servicios
        client_service = container.get_client_service()
        pet_service = container.get_pet_service()
        appointment_service = container.get_appointment_service()
        
        # Obtener estadísticas básicas
        try:
            all_clients = client_service.get_all_clients()
            total_clients = len(all_clients) if all_clients else 0
        except:
            total_clients = 0
        
        try:
            all_pets = pet_service.get_all_pets()
            total_pets = len(all_pets) if all_pets else 0
        except:
            total_pets = 0
        
        # Estadísticas básicas
        stats = {
            'total_clients': total_clients,
            'total_pets': total_pets,
            'appointments_today': 0,  # Por ahora 0
            'upcoming_appointments': 0  # Por ahora 0
        }
        
        return render_template(
            'dashboard/index.html',
            stats=stats,
            today_schedule=[],  # Lista vacía por ahora
            upcoming_appointments=[],  # Lista vacía por ahora
            appointment_stats={
                'scheduled': 0,
                'confirmed': 0,
                'completed': 0,
                'cancelled': 0
            },
            today=date.today()
        )
        
    except Exception as e:
        print(f"Error en dashboard: {e}")
        
        # Datos de fallback seguros
        return render_template(
            'dashboard/index.html',
            stats={
                'total_clients': 0,
                'total_pets': 0,
                'appointments_today': 0,
                'upcoming_appointments': 0
            },
            today_schedule=[],
            upcoming_appointments=[],
            appointment_stats={
                'scheduled': 0,
                'confirmed': 0,
                'completed': 0,
                'cancelled': 0
            },
            today=date.today()
        )

@dashboard_bp.route('/quick-stats')
def quick_stats():
    """
    RUTA: Estadísticas rápidas (para AJAX)
    Retorna JSON con estadísticas actualizadas
    """
    try:
        container = get_container()
        
        client_service = container.get_client_service()
        pet_service = container.get_pet_service()
        appointment_service = container.get_appointment_service()
        
        today = date.today()
        
        stats = {
            'clients': len(client_service.get_all_clients()),
            'pets': len(pet_service.get_all_pets()),
            'appointments_today': len(appointment_service.get_appointments_by_date(today)),
            'upcoming': len(appointment_service.get_upcoming_appointments(24))
        }
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error en quick-stats: {e}")
        return jsonify({'error': 'Error loading stats'}), 500

@dashboard_bp.route('/users')
def users():
    """
    RUTA: Gestión de usuarios (solo para admins)
    Muestra lista de usuarios del sistema
    """
    # Verificar permisos de admin
    try:
        container = get_container()
        user_repo = container.get_user_repository()
        current_user = user_repo.find_by_id(session['user_id'])
        
        if not current_user or current_user.role.value != 'admin':
            flash('No tienes permisos para acceder a esta página.', 'error')
            return redirect(url_for('dashboard.index'))
    
    except Exception as e:
        flash('Error verificando permisos.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        # Obtener todos los usuarios
        all_users = user_repo.find_all()
        
        return render_template('dashboard/users.html', users=all_users)
        
    except Exception as e:
        print(f"Error cargando usuarios: {e}")
        flash('Error cargando lista de usuarios.', 'error')
        return render_template('dashboard/users.html', users=[])

@dashboard_bp.route('/reports')
def reports():
    """
    RUTA: Reportes básicos de la clínica
    """
    try:
        container = get_container()
        
        appointment_service = container.get_appointment_service()
        
        # Reportes de la última semana
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        week_appointments = appointment_service.find_by_date_range(start_date, end_date)
        
        # Agrupar por día
        daily_counts = {}
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_key = day.strftime('%Y-%m-%d')
            daily_counts[day_key] = {
                'date': day.strftime('%d/%m'),
                'count': 0,
                'day_name': day.strftime('%A')
            }
        
        for appointment in week_appointments:
            day_key = appointment.appointment_date.strftime('%Y-%m-%d')
            if day_key in daily_counts:
                daily_counts[day_key]['count'] += 1
        
        # Convertir a lista ordenada
        daily_report = list(daily_counts.values())
        
        return render_template(
            'dashboard/reports.html',
            daily_report=daily_report,
            total_week_appointments=len(week_appointments)
        )
        
    except Exception as e:
        print(f"Error en reportes: {e}")
        flash('Error cargando reportes.', 'error')
        return render_template('dashboard/reports.html', daily_report=[], total_week_appointments=0)