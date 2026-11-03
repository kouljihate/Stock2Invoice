import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.services.order_service import OrderService
from app.core.models.order_model import CustomerOrderModel
from app.core.models.product_model import ProductModel
from app.core.models.customer_model import CustomerModel
from app.core.models.user_model import UserModel
from app.core.services.event_service import EventService
from app.core.utils.helpers import paginate, oid, tenant_filter

logger = logging.getLogger(__name__)
web_orders_bp = Blueprint('web_orders', __name__, template_folder='../../../templates')


def _get_user():
    """Acting user document, resolved from the database (never claims)."""
    from app.core.utils.context import current_user
    return current_user()


def _company_id():
    """Acting user's company id, resolved from the database (never claims)."""
    from app.core.utils.context import current_company_id
    return current_company_id()


@web_orders_bp.route('')
@web_orders_bp.route('/')
@jwt_required()
def list_orders():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args['status']
        cid = _company_id()
        items, total = OrderService.list(page, per_page, filters, cid)
        user = _get_user()
        return render_template('orders/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               orders=items, total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception as e:
        logger.exception('Order list error')
        flash('Could not load orders.', 'danger')
        return render_template('orders/list.html', mode='web',
                               orders=[], total=0, page=1, per_page=20, pages=0)


@web_orders_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_order():
    user = _get_user()
    cid = _company_id()
    if request.method == 'GET':
        customers = CustomerModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
        products = ProductModel.find_all_unpaginated(tenant_filter(cid))
        return render_template('orders/edit.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               order=None, products=products,
                               customers=[CustomerModel.to_dict(c) for c in customers])

    try:
        data = request.form.to_dict(flat=False)
        items = []
        skus = data.get('sku', [])
        qtys = data.get('quantity', [])
        prices = data.get('unit_price', [])
        names = data.get('name', [])
        package_types = data.get('package_type', [])
        pack_sizes = data.get('pack_size', [])
        pack_size_units = data.get('pack_size_unit', [])
        existing_qtys = data.get('existing_qty', [])
        qty_errors = []
        for i in range(len(skus)):
            if skus[i] and qtys[i] and int(qtys[i]) > 0:
                qty = int(qtys[i])
                exist_qty = int(existing_qtys[i]) if i < len(existing_qtys) and existing_qtys[i] else 0
                item_name = names[i] if i < len(names) else skus[i]
                if exist_qty > 0 and qty > exist_qty:
                    qty_errors.append(f"'{item_name}': qty {qty} exceeds stock {exist_qty}")
                items.append({'sku': skus[i], 'quantity': qty,
                              'unit_price': float(prices[i]) if prices[i] else 0,
                              'name': names[i] if i < len(names) else '',
                              'package_type': package_types[i] if i < len(package_types) else '',
                              'pack_size': pack_sizes[i] if i < len(pack_sizes) else '',
                              'pack_size_unit': pack_size_units[i] if i < len(pack_size_units) else '',
                              'existing_qty': exist_qty})
        if qty_errors:
            flash('Quantity exceeds available stock', 'danger')
            return redirect(url_for('web_orders.create_order'))

        payload = {
            'customer_name': request.form.get('customer_name', ''),
            'contact_name': request.form.get('contact_name', ''),
            'contact_email': request.form.get('contact_email', ''),
            'customer_address': request.form.get('customer_address', ''),
            'items': items,
            'discount_percent': request.form.get('discount_percent', 0),
            'tax_percent': request.form.get('tax_percent', 10),
            'status': request.form.get('status', 'pending'),
            'notes': request.form.get('notes', ''),
        }

        errors = OrderService.validate(payload, cid)
        if errors:
            for e in errors:
                flash(e, 'danger')
            customers = CustomerModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
            products = ProductModel.find_all_unpaginated(tenant_filter(cid))
            return render_template('orders/edit.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None,
                                   order=payload, products=products,
                                   customers=[CustomerModel.to_dict(c) for c in customers])

        user_id = get_jwt_identity()
        order_id, order_number = OrderService.create(payload, user_id, cid)
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'order', order_id, order_number, 'created', user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash(f'Customer Order {order_number} created.', 'success')
        return redirect(url_for('web_orders.view_order', order_id=order_id))
    except Exception as e:
        logger.exception('Order create error')
        flash('Could not create order.', 'danger')
        customers = CustomerModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
        products = ProductModel.find_all_unpaginated(tenant_filter(cid))
        return render_template('orders/edit.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               order=request.form, products=products,
                               customers=[CustomerModel.to_dict(c) for c in customers])


@web_orders_bp.route('/<order_id>')
@jwt_required()
def view_order(order_id):
    user = _get_user()
    cid = _company_id()
    order = OrderService.get_by_id(order_id, cid)
    if not order:
        flash('Order not found.', 'danger')
        return redirect(url_for('web_orders.list_orders'))
    return render_template('orders/detail.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           order=order)


@web_orders_bp.route('/<order_id>/status', methods=['POST'])
@jwt_required()
def update_status(order_id):
    try:
        status = request.form.get('status')
        if status not in ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled'):
            flash('Invalid status.', 'danger')
            return redirect(url_for('web_orders.view_order', order_id=order_id))
        user_id = get_jwt_identity()
        cid = _company_id()
        order = OrderService.get_by_id(order_id, cid)
        old_status = order.get('status') if order else ''
        OrderService.update(order_id, {'status': status}, user_id, cid)
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'order', order_id, order.get('order_number',''), 'status_changed',
                            changes={'from': old_status, 'to': status},
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Order status updated.', 'success')
    except Exception as e:
        logger.exception('Order status update error')
        flash('Could not update status.', 'danger')
    return redirect(url_for('web_orders.view_order', order_id=order_id))


@web_orders_bp.route('/<order_id>/delete', methods=['POST'])
@jwt_required()
def delete_order(order_id):
    order = CustomerOrderModel.find_by_id(order_id)
    if not order:
        flash('Order not found.', 'danger')
    else:
        cid = _company_id()
        if str(order.get('company_id', '')) != str(cid):
            flash('Access denied.', 'danger')
            return redirect(url_for('web_orders.list_orders'))
        user_id = get_jwt_identity()
        user_obj = UserModel.find_by_id(user_id)
        order_number = order.get('order_number', '')
        CustomerOrderModel.delete(order_id)
        EventService.record(cid, 'order', order_id, order_number, 'deleted', user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Order deleted.', 'success')
    return redirect(url_for('web_orders.list_orders'))


@web_orders_bp.route('/<order_id>/pdf')
@jwt_required()
def download_pdf(order_id):
    try:
        import io
        from weasyprint import HTML
        user = _get_user()
        cid = _company_id()
        order = OrderService.get_by_id(order_id, cid)
        if not order:
            flash('Order not found.', 'danger')
            return redirect(url_for('web_orders.list_orders'))

        cid = _company_id()
        current_company = None
        if cid:
            from app.core.models.company_model import CompanyModel
            company = CompanyModel.find_by_id(cid)
            if company:
                current_company = CompanyModel.to_dict(company)

        from datetime import datetime
        html = render_template('orders/printable.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               order=order, current_company=current_company,
                               current_lang=request.cookies.get('lang', 'en'),
                               now=datetime.now)
        pdf = HTML(string=html).write_pdf()
        buf = io.BytesIO(pdf)
        buf.seek(0)
        return send_file(buf, mimetype='application/pdf', as_attachment=True,
                         download_name=f'order-{order["order_number"]}.pdf')
    except Exception as e:
        logger.exception('Order PDF generation error')
        flash(f'Could not generate PDF: {e}', 'danger')
        return redirect(url_for('web_orders.view_order', order_id=order_id))
