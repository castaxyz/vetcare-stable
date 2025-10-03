"""
EXPLICACIÓN: Blueprint para gestión completa de facturación.
Implementa CRUD completo de facturas, items y reportes de facturación.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date, timedelta
from decimal import Decimal

from infra import get_container
from domain.entities.invoice import InvoiceStatus

# Crear blueprint
invoices_bp = Blueprint('invoices', __name__, template_folder='../templates/invoices')

@invoices_bp.route('/')
def list_invoices():
    """
    RUTA: Lista de todas las facturas
    Incluye filtros por estado y búsqueda
    """
    try:
        container = get_container()
        invoice_service = container.get_invoice_service()
        
        # Obtener filtros
        status_filter = request.args.get('status', '').strip()
        search_query = request.args.get('search', '').strip()
        
        if status_filter and status_filter != 'all':
            invoices = invoice_service.get_invoices_by_status(InvoiceStatus(status_filter))
            flash(f'Mostrando facturas con estado: {status_filter}', 'info')
        else:
            invoices = invoice_service.get_all_invoices()
        
        # Filtrar por búsqueda si se proporciona
        if search_query:
            invoices = [inv for inv in invoices if 
                       search_query.lower() in inv.invoice_number.lower() or
                       search_query.lower() in str(inv.client_id)]
            flash(f'Encontradas {len(invoices)} facturas para "{search_query}"', 'info')
        
        return render_template('invoices/list.html', 
                             invoices=invoices, 
                             status_filter=status_filter,
                             search_query=search_query,
                             invoice_statuses=InvoiceStatus)
        
    except Exception as e:
        print(f"Error listando facturas: {e}")
        flash('Error cargando lista de facturas.', 'error')
        return render_template('invoices/list.html', invoices=[], 
                             status_filter='', search_query='',
                             invoice_statuses=InvoiceStatus)

@invoices_bp.route('/create', methods=['GET', 'POST'])
def create_invoice():
    """
    RUTA: Crear nueva factura
    GET: Muestra formulario
    POST: Procesa creación
    """
    # Importar localmente para asegurar disponibilidad en GET y POST
    from datetime import date, datetime
    from decimal import Decimal

    if request.method == 'GET':
        try:
            container = get_container()
            client_service = container.get_client_service()
            appointment_service = container.get_appointment_service()
            product_service = container.get_product_service()

            clients = client_service.get_all_clients()
            appointments = appointment_service.get_all_appointments()  # Usar método que existe
            products = product_service.get_active_products()

            today = date.today().strftime('%Y-%m-%d')

            return render_template('invoices/create.html',
                                 clients=clients,
                                 appointments=appointments,
                                 products=products,
                                 today=today)
        except Exception as e:
            print(f"Error cargando formulario de factura: {e}")
            flash('Error cargando formulario.', 'error')
            return redirect(url_for('invoices.list_invoices'))

    try:
        container = get_container()
        invoice_service = container.get_invoice_service()

        # Obtener datos básicos de la factura
        invoice_data = {
            'client_id': int(request.form['client_id']),
            'appointment_id': int(request.form['appointment_id']) if request.form.get('appointment_id') else None,
            'issue_date': datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date() if request.form.get('issue_date') else date.today(),
            'due_date': datetime.strptime(request.form['due_date'], '%Y-%m-%d').date() if request.form.get('due_date') else None,
            'tax_percentage': Decimal(request.form.get('tax_percentage', '0')),
            'notes': request.form.get('notes', '').strip() or None,
            'status': InvoiceStatus.PENDING  # Usar el enum directamente
        }

        # Procesar items de la factura
        items = []
        form_data = request.form.to_dict()

        # Buscar todos los items en el formulario
        item_indices = set()
        for key in form_data.keys():
            if key.startswith('items[') and '][' in key:
                # Extraer el índice del item (ej: items[1][description] -> 1)
                index = key.split('[')[1].split(']')[0]
                item_indices.add(index)

        # Procesar cada item
        for index in item_indices:
            description = form_data.get(f'items[{index}][description]', '').strip()
            if description:  # Solo agregar items con descripción
                item_data = {
                    'product_id': int(form_data[f'items[{index}][product_id]']) if form_data.get(f'items[{index}][product_id]') else None,
                    'description': description,
                    'quantity': int(form_data.get(f'items[{index}][quantity]', 1)),
                    'unit_price': Decimal(form_data.get(f'items[{index}][unit_price]', '0')),
                    'discount_percentage': Decimal(form_data.get(f'items[{index}][discount_percentage]', '0'))
                }
                items.append(item_data)

        if not items:
            flash('Debe agregar al menos un item a la factura.', 'error')
            return redirect(url_for('invoices.create_invoice'))

        invoice_data['items'] = items

        # Crear la factura
        invoice = invoice_service.create_invoice(invoice_data)

        flash(f'Factura {invoice.invoice_number} creada exitosamente.', 'success')
        return redirect(url_for('invoices.list_invoices'))

    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'error')
        return redirect(url_for('invoices.create_invoice'))
    except Exception as e:
        print(f"Error creando factura: {e}")
        flash('Error creando factura.', 'error')
        return redirect(url_for('invoices.create_invoice'))

@invoices_bp.route('/<int:invoice_id>')
def view_invoice(invoice_id):
    """
    RUTA: Ver detalles de una factura específica
    """
    try:
        container = get_container()
        invoice_service = container.get_invoice_service()
        client_service = container.get_client_service()
        
        invoice = invoice_service.get_invoice_by_id(invoice_id)
        if not invoice:
            flash('Factura no encontrada.', 'error')
            return redirect(url_for('invoices.list_invoices'))
        
        client = client_service.get_client_by_id(invoice.client_id)
        
        return render_template('invoices/view.html', 
                             invoice=invoice, 
                             client=client)
        
    except Exception as e:
        print(f"Error viendo factura: {e}")
        flash('Error cargando factura.', 'error')
        return redirect(url_for('invoices.list_invoices'))

@invoices_bp.route('/<int:invoice_id>/add_item', methods=['POST'])
def add_item_to_invoice(invoice_id):
    """
    RUTA: Agregar item a factura existente
    """
    try:
        container = get_container()
        invoice_service = container.get_invoice_service()
        
        item_data = {
            'product_id': int(request.form['product_id']) if request.form.get('product_id') else None,
            'description': request.form['description'],
            'quantity': int(request.form['quantity']),
            'unit_price': Decimal(request.form['unit_price']),
            'discount_percentage': Decimal(request.form.get('discount_percentage', '0'))
        }
        
        invoice = invoice_service.add_item_to_invoice(invoice_id, item_data)
        
        flash('Item agregado exitosamente.', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice.id))
        
    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'error')
    except Exception as e:
        print(f"Error agregando item: {e}")
        flash('Error agregando item a la factura.', 'error')
    
    return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))

@invoices_bp.route('/<int:invoice_id>/update_status', methods=['POST'])
def update_invoice_status(invoice_id):
    """
    RUTA: Actualizar estado de factura
    """
    try:
        container = get_container()
        invoice_service = container.get_invoice_service()
        
        new_status = InvoiceStatus(request.form['status'])
        invoice = invoice_service.update_invoice_status(invoice_id, new_status)
        
        flash(f'Estado de factura actualizado a: {new_status.value}', 'success')
        return redirect(url_for('invoices.view_invoice', invoice_id=invoice.id))
        
    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'error')
    except Exception as e:
        print(f"Error actualizando estado: {e}")
        flash('Error actualizando estado de factura.', 'error')
    
    return redirect(url_for('invoices.view_invoice', invoice_id=invoice_id))

@invoices_bp.route('/overdue')
def overdue_invoices():
    """
    RUTA: Lista de facturas vencidas
    """
    try:
        container = get_container()
        invoice_service = container.get_invoice_service()
        
        overdue_invoices = invoice_service.get_overdue_invoices()
        
        return render_template('invoices/overdue.html', 
                             invoices=overdue_invoices)
        
    except Exception as e:
        print(f"Error cargando facturas vencidas: {e}")
        flash('Error cargando facturas vencidas.', 'error')
        return render_template('invoices/overdue.html', invoices=[])

@invoices_bp.route('/reports')
def revenue_reports():
    """
    RUTA: Reportes de ingresos
    """
    try:
        container = get_container()
        invoice_service = container.get_invoice_service()
        
        # Obtener parámetros de fecha
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            # Por defecto, último mes
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
        
        report = invoice_service.get_revenue_report(start_date, end_date)
        
        return render_template('invoices/reports.html', 
                             report=report,
                             start_date=start_date,
                             end_date=end_date)
        
    except Exception as e:
        print(f"Error generando reporte: {e}")
        flash('Error generando reporte de ingresos.', 'error')
        return render_template('invoices/reports.html', 
                             report=None,
                             start_date=date.today() - timedelta(days=30),
                             end_date=date.today())

# API endpoints para AJAX
@invoices_bp.route('/api/client/<int:client_id>/appointments')
def get_client_appointments(client_id):
    """
    API: Obtener citas de un cliente específico
    """
    try:
        container = get_container()
        appointment_service = container.get_appointment_service()

        # Por ahora retornamos lista vacía hasta implementar el método
        appointments = []

        return jsonify([{
            'id': apt.id,
            'date': apt.appointment_date.strftime('%Y-%m-%d %H:%M'),
            'type': apt.appointment_type.value,
            'pet_name': 'N/A'  # Necesitaríamos cargar la mascota
        } for apt in appointments])
        
    except Exception as e:
        print(f"Error obteniendo citas del cliente: {e}")
        return jsonify([]), 500

@invoices_bp.route('/api/product/<int:product_id>')
def get_product_details(product_id):
    """
    API: Obtener detalles de un producto
    """
    try:
        container = get_container()
        product_service = container.get_product_service()
        
        product = product_service.get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'unit_price': float(product.unit_price),
            'sku': product.sku
        })
        
    except Exception as e:
        print(f"Error obteniendo detalles del producto: {e}")
        return jsonify({'error': 'Internal server error'}), 500