import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.services.order_service import OrderService
from app.core.models.order_model import OrderModel
from app.core.models.product_model import ProductModel
from app.core.models.user_model import UserModel
from app.core.utils.helpers import paginate, oid

logger = logging.getLogger(__name__)
web_orders_bp = Blueprint('web_orders', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


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
        products = ProductModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else ProductModel.find_all_unpaginated()
        return render_template('orders/edit.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               order=None, products=products)

    try:
        data = request.form.to_dict(flat=False)
        items = []
        skus = data.get('sku', [])
        qtys = data.get('quantity', [])
        prices = data.get('unit_price', [])
        names = data.get('name', [])
        for i in range(len(skus)):
            if skus[i] and qtys[i] and int(qtys[i]) > 0:
                items.append({'sku': skus[i], 'quantity': qtys[i],
                              'unit_price': prices[i] if prices[i] else 0,
                              'name': names[i] if i < len(names) else ''})

        payload = {
            'customer_name': request.form.get('customer_name', ''),
            'customer_email': request.form.get('customer_email', ''),
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
            products = ProductModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else ProductModel.find_all_unpaginated()
            return render_template('orders/edit.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None,
                                   order=payload, products=products)

        user_id = get_jwt_identity()
        order_id, order_number = OrderService.create(payload, user_id, cid)
        flash(f'Order {order_number} created.', 'success')
        return redirect(url_for('web_orders.view_order', order_id=order_id))
    except Exception as e:
        logger.exception('Order create error')
        flash('Could not create order.', 'danger')
        products = ProductModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else ProductModel.find_all_unpaginated()
        return render_template('orders/edit.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               order=request.form, products=products)


@web_orders_bp.route('/<order_id>')
@jwt_required()
def view_order(order_id):
    user = _get_user()
    order = OrderService.get_by_id(order_id)
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
        OrderService.update(order_id, {'status': status}, user_id, cid)
        flash('Order status updated.', 'success')
    except Exception as e:
        logger.exception('Order status update error')
        flash('Could not update status.', 'danger')
    return redirect(url_for('web_orders.view_order', order_id=order_id))


@web_orders_bp.route('/<order_id>/delete', methods=['POST'])
@jwt_required()
def delete_order(order_id):
    order = OrderModel.find_by_id(order_id)
    if not order:
        flash('Order not found.', 'danger')
    else:
        OrderModel.delete(order_id)
        flash('Order deleted.', 'success')
    return redirect(url_for('web_orders.list_orders'))


@web_orders_bp.route('/<order_id>/pdf')
@jwt_required()
def download_pdf(order_id):
    try:
        import io
        from weasyprint import HTML
        user = _get_user()
        order = OrderService.get_by_id(order_id)
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
