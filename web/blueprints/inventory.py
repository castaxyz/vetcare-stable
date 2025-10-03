"""
EXPLICACIÓN: Blueprint para gestión completa de inventario.
Implementa CRUD de productos, categorías, control de stock y alertas.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
from decimal import Decimal

from infra import get_container
from domain.entities.product import ProductStatus, ProductType
from domain.entities.stock import StockMovementType

# Crear blueprint
inventory_bp = Blueprint('inventory', __name__, template_folder='../templates/inventory')

# Rutas para productos
@inventory_bp.route('/products')
def list_products():
    """
    RUTA: Lista de todos los productos
    Incluye filtros por categoría, tipo y estado
    """
    try:
        container = get_container()
        product_service = container.get_product_service()
        category_service = container.get_category_service()
        
        # Obtener filtros
        category_filter = request.args.get('category', '').strip()
        type_filter = request.args.get('type', '').strip()
        status_filter = request.args.get('status', '').strip()
        search_query = request.args.get('search', '').strip()
        
        # Aplicar filtros
        if search_query:
            products = product_service.search_products(search_query)
        elif category_filter and category_filter != 'all':
            products = product_service.get_products_by_category(int(category_filter))
        elif type_filter and type_filter != 'all':
            products = product_service.get_products_by_type(ProductType(type_filter))
        elif status_filter and status_filter != 'all':
            products = product_service.get_products_by_status(ProductStatus(status_filter))
        else:
            products = product_service.get_all_products()
        
        categories = category_service.get_active_categories()
        
        return render_template('inventory/products/list.html', 
                             products=products,
                             categories=categories,
                             product_types=ProductType,
                             product_statuses=ProductStatus,
                             category_filter=category_filter,
                             type_filter=type_filter,
                             status_filter=status_filter,
                             search_query=search_query)
        
    except Exception as e:
        print(f"Error listando productos: {e}")
        flash('Error cargando lista de productos.', 'error')
        return render_template('inventory/products/list.html', products=[])

@inventory_bp.route('/products/add', methods=['GET', 'POST'])
@inventory_bp.route('/products/create', methods=['GET', 'POST'])
def add_product():
    """
    RUTA: Crear nuevo producto
    GET: Muestra formulario
    POST: Procesa creación
    """
    if request.method == 'GET':
        try:
            container = get_container()
            category_service = container.get_category_service()

            categories = category_service.get_active_categories()

            return render_template('inventory/products/add.html',
                                 categories=categories,
                                 product_types=ProductType,
                                 product_statuses=ProductStatus)
        except Exception as e:
            print(f"Error cargando formulario de producto: {e}")
            flash('Error cargando formulario.', 'error')
            return redirect(url_for('inventory.list_products'))

    try:
        container = get_container()
        product_service = container.get_product_service()

        # Obtener datos del formulario
        product_data = {
            'name': request.form['name'],
            'description': request.form.get('description', '').strip() or None,
            'sku': request.form['sku'],
            'category_id': int(request.form['category_id']) if request.form.get('category_id') else None,
            'product_type': request.form['product_type'],
            'unit_price': Decimal(request.form['unit_price']),
            'cost_price': Decimal(request.form['cost_price']) if request.form.get('cost_price') else Decimal('0'),
            'status': ProductStatus.ACTIVE.value,  # Por defecto activo - usar .value
            'minimum_stock': int(request.form.get('minimum_stock', 0)),
            'maximum_stock': int(request.form.get('maximum_stock', 0)) if request.form.get('maximum_stock') else None,
            'reorder_point': int(request.form.get('reorder_point', 0)) if request.form.get('reorder_point') else None,
            'supplier': request.form.get('supplier', '').strip() or None,
            'expiration_tracking': bool(request.form.get('expiration_tracking'))
        }

        # Crear producto
        product = product_service.create_product(product_data)

        flash(f'Producto "{product.name}" creado exitosamente.', 'success')
        return redirect(url_for('inventory.list_products'))

    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'error')
        return redirect(url_for('inventory.add_product'))
    except Exception as e:
        print(f"Error creando producto: {e}")
        flash('Error creando producto. Intente nuevamente.', 'error')
        return redirect(url_for('inventory.add_product'))

@inventory_bp.route('/products/<int:product_id>')
def view_product(product_id):
    """
    RUTA: Ver detalles de un producto específico
    """
    try:
        container = get_container()
        product_service = container.get_product_service()
        inventory_service = container.get_inventory_service()
        
        product = product_service.get_product_by_id(product_id)
        if not product:
            flash('Producto no encontrado.', 'error')
            return redirect(url_for('inventory.list_products'))
        
        stocks = inventory_service.get_stock_by_product(product_id)
        movements = inventory_service.get_stock_movements(product_id)
        
        return render_template('inventory/products/view.html', 
                             product=product,
                             stocks=stocks,
                             movements=movements[:10])  # Últimos 10 movimientos
        
    except Exception as e:
        print(f"Error viendo producto: {e}")
        flash('Error cargando producto.', 'error')
        return redirect(url_for('inventory.list_products'))

@inventory_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    """
    RUTA: Editar producto existente
    """
    if request.method == 'GET':
        try:
            container = get_container()
            product_service = container.get_product_service()
            category_service = container.get_category_service()
            
            product = product_service.get_product_by_id(product_id)
            if not product:
                flash('Producto no encontrado.', 'error')
                return redirect(url_for('inventory.list_products'))
            
            categories = category_service.get_active_categories()
            
            return render_template('inventory/products/edit.html', 
                                 product=product,
                                 categories=categories,
                                 product_types=ProductType,
                                 product_statuses=ProductStatus)
        except Exception as e:
            print(f"Error cargando formulario de edición: {e}")
            flash('Error cargando formulario.', 'error')
            return redirect(url_for('inventory.list_products'))
    
    try:
        container = get_container()
        product_service = container.get_product_service()
        
        # Obtener datos del formulario
        product_data = {
            'name': request.form['name'],
            'description': request.form.get('description', '').strip() or None,
            'sku': request.form['sku'],
            'category_id': int(request.form['category_id']) if request.form.get('category_id') else None,
            'product_type': request.form['product_type'],
            'unit_price': Decimal(request.form['unit_price']),
            'cost_price': Decimal(request.form['cost_price']),
            'status': request.form.get('status', ProductStatus.ACTIVE.value),
            'minimum_stock': int(request.form.get('minimum_stock', 0)),
            'maximum_stock': int(request.form['maximum_stock']) if request.form.get('maximum_stock') else None,
            'reorder_point': int(request.form.get('reorder_point', 0)),
            'supplier': request.form.get('supplier', '').strip() or None,
            'expiration_tracking': 'expiration_tracking' in request.form
        }
        
        product = product_service.update_product(product_id, product_data)
        
        flash(f'Producto "{product.name}" actualizado exitosamente.', 'success')
        return redirect(url_for('inventory.view_product', product_id=product.id))
        
    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'error')
        return redirect(url_for('inventory.edit_product', product_id=product_id))
    except Exception as e:
        print(f"Error actualizando producto: {e}")
        flash('Error actualizando producto.', 'error')
        return redirect(url_for('inventory.edit_product', product_id=product_id))

# Rutas para stock
@inventory_bp.route('/stock')
def stock_overview():
    """
    RUTA: Vista general del stock
    """
    try:
        container = get_container()
        inventory_service = container.get_inventory_service()
        product_service = container.get_product_service()
        
        low_stock_alerts = inventory_service.get_low_stock_alerts()
        expiration_alerts = inventory_service.get_expiration_alerts()
        
        return render_template('inventory/stock/overview.html',
                             low_stock_alerts=low_stock_alerts,
                             expiration_alerts=expiration_alerts)
        
    except Exception as e:
        print(f"Error cargando vista de stock: {e}")
        flash('Error cargando vista de stock.', 'error')
        return render_template('inventory/stock/overview.html',
                             low_stock_alerts=[],
                             expiration_alerts=[])

@inventory_bp.route('/stock/add', methods=['GET', 'POST'])
def add_stock():
    """
    RUTA: Agregar stock (entrada de inventario)
    """
    if request.method == 'GET':
        try:
            container = get_container()
            product_service = container.get_product_service()
            
            products = product_service.get_active_products()
            
            return render_template('inventory/stock/add.html', products=products)
        except Exception as e:
            print(f"Error cargando formulario de stock: {e}")
            flash('Error cargando formulario.', 'error')
            return redirect(url_for('inventory.stock_overview'))
    
    try:
        container = get_container()
        inventory_service = container.get_inventory_service()
        
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])
        expiration_date = None
        if request.form.get('expiration_date'):
            expiration_date = datetime.strptime(request.form['expiration_date'], '%Y-%m-%d').date()
        
        batch_number = request.form.get('batch_number', '').strip() or None
        location = request.form.get('location', '').strip() or None
        notes = request.form.get('notes', '').strip() or None
        
        stock = inventory_service.add_stock(
            product_id=product_id,
            quantity=quantity,
            expiration_date=expiration_date,
            batch_number=batch_number,
            location=location,
            notes=notes
        )
        
        flash(f'Stock agregado exitosamente. Cantidad: {quantity}', 'success')
        return redirect(url_for('inventory.stock_overview'))
        
    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'error')
        return redirect(url_for('inventory.add_stock'))
    except Exception as e:
        print(f"Error agregando stock: {e}")
        flash('Error agregando stock.', 'error')
        return redirect(url_for('inventory.add_stock'))

@inventory_bp.route('/stock/adjust', methods=['GET', 'POST'])
def adjust_stock():
    """
    RUTA: Ajustar stock (corrección de inventario)
    """
    if request.method == 'GET':
        try:
            container = get_container()
            product_service = container.get_product_service()
            
            products = product_service.get_active_products()
            
            return render_template('inventory/stock/adjust.html', products=products)
        except Exception as e:
            print(f"Error cargando formulario de ajuste: {e}")
            flash('Error cargando formulario.', 'error')
            return redirect(url_for('inventory.stock_overview'))
    
    try:
        container = get_container()
        inventory_service = container.get_inventory_service()
        
        product_id = int(request.form['product_id'])
        new_quantity = int(request.form['new_quantity'])
        reason = request.form['reason']
        
        stock = inventory_service.adjust_stock(product_id, new_quantity, reason)
        
        flash(f'Stock ajustado exitosamente. Nueva cantidad: {new_quantity}', 'success')
        return redirect(url_for('inventory.stock_overview'))
        
    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'error')
        return redirect(url_for('inventory.adjust_stock'))
    except Exception as e:
        print(f"Error ajustando stock: {e}")
        flash('Error ajustando stock.', 'error')
        return redirect(url_for('inventory.adjust_stock'))

# Rutas para categorías
@inventory_bp.route('/categories')
def list_categories():
    """
    RUTA: Lista de categorías
    """
    try:
        container = get_container()
        category_service = container.get_category_service()
        
        categories = category_service.get_category_hierarchy()
        
        return render_template('inventory/categories/list.html', categories=categories)
        
    except Exception as e:
        print(f"Error listando categorías: {e}")
        flash('Error cargando lista de categorías.', 'error')
        return render_template('inventory/categories/list.html', categories=[])

@inventory_bp.route('/categories/create', methods=['GET', 'POST'])
def create_category():
    """
    RUTA: Crear nueva categoría
    """
    if request.method == 'GET':
        try:
            container = get_container()
            category_service = container.get_category_service()
            
            parent_categories = category_service.get_active_categories()
            
            return render_template('inventory/categories/create.html', 
                                 parent_categories=parent_categories)
        except Exception as e:
            print(f"Error cargando formulario de categoría: {e}")
            flash('Error cargando formulario.', 'error')
            return redirect(url_for('inventory.list_categories'))
    
    try:
        container = get_container()
        category_service = container.get_category_service()
        
        category_data = {
            'name': request.form['name'],
            'description': request.form.get('description', '').strip() or None,
            'parent_id': int(request.form['parent_id']) if request.form.get('parent_id') else None,
            'is_active': 'is_active' in request.form
        }
        
        category = category_service.create_category(category_data)
        
        flash(f'Categoría "{category.name}" creada exitosamente.', 'success')
        return redirect(url_for('inventory.list_categories'))
        
    except ValueError as e:
        flash(f'Error de validación: {str(e)}', 'error')
        return redirect(url_for('inventory.create_category'))
    except Exception as e:
        print(f"Error creando categoría: {e}")
        flash('Error creando categoría.', 'error')
        return redirect(url_for('inventory.create_category'))

# API endpoints
@inventory_bp.route('/api/product/<int:product_id>/stock')
def get_product_stock(product_id):
    """
    API: Obtener stock actual de un producto
    """
    try:
        container = get_container()
        inventory_service = container.get_inventory_service()
        
        stocks = inventory_service.get_stock_by_product(product_id)
        total_stock = sum(stock.current_quantity for stock in stocks)
        available_stock = sum(stock.available_quantity for stock in stocks)
        
        return jsonify({
            'total_stock': total_stock,
            'available_stock': available_stock,
            'reserved_stock': total_stock - available_stock,
            'stocks': [{
                'id': stock.id,
                'quantity': stock.current_quantity,
                'available': stock.available_quantity,
                'expiration_date': stock.expiration_date.isoformat() if stock.expiration_date else None,
                'batch_number': stock.batch_number,
                'location': stock.location
            } for stock in stocks]
        })
        
    except Exception as e:
        print(f"Error obteniendo stock del producto: {e}")
        return jsonify({'error': 'Internal server error'}), 500