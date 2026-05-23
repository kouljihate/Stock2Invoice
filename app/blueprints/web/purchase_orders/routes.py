import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.purchase_order_model import PurchaseOrderModel
from app.core.models.supplier_model import SupplierModel
from app.core.utils.helpers import paginate, oid

logger = logging.getLogger(__name__)
web_purchase_orders_bp = Blueprint('web_purchase_orders', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_purchase_orders_bp.route('')
@web_purchase_orders_bp.route('/')
@jwt_required()
def list_orders():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = {'company_id': ObjectId(cid)} if cid else {}
        if request.args.get('status'):
            filters['status'] = request.args['status']
        items, total = PurchaseOrderModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('purchase_orders/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               orders=[PurchaseOrderModel.to_dict(o) for o in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('PO list error')
        return render_template('purchase_orders/list.html', mode='web', orders=[], total=0, page=1, per_page=20, pages=0)


@web_purchase_orders_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_order():
    user = _get_user()
    cid = _company_id()
    if request.method == 'GET':
        suppliers = SupplierModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
        return render_template('purchase_orders/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               order=None, suppliers=suppliers)
    try:
        cid = _company_id()
        from datetime import datetime
        data = request.form.to_dict(flat=False)
        items = []
        skus = data.get('sku', [])
        qtys = data.get('quantity', [])
        prices = data.get('unit_price', [])
        names = data.get('name', [])
        for i in range(len(skus)):
            if skus[i] and qtys[i] and int(qtys[i]) > 0:
                items.append({'sku': skus[i], 'quantity': int(qtys[i]),
                              'unit_price': float(prices[i]) if prices[i] else 0,
                              'name': names[i] if i < len(names) else ''})
        count = PurchaseOrderModel.count({'company_id': oid(cid)})
        po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
        payload = {
            'po_number': po_number,
            'supplier_id': oid(request.form.get('supplier_id', '')),
            'supplier_name': request.form.get('supplier_name', ''),
            'items': items,
            'subtotal': sum(it['quantity'] * it['unit_price'] for it in items),
            'discount_percent': float(request.form.get('discount_percent', 0)),
            'tax_percent': float(request.form.get('tax_percent', 0)),
            'notes': request.form.get('notes', ''),
            'status': 'draft',
            'company_id': oid(cid),
            'created_by': oid(get_jwt_identity()),
        }
        discount = payload['subtotal'] * payload['discount_percent'] / 100
        taxable = payload['subtotal'] - discount
        payload['discount_amount'] = discount
        payload['tax_amount'] = taxable * payload['tax_percent'] / 100
        payload['total'] = taxable + payload['tax_amount']
        PurchaseOrderModel.create(payload)
        flash(f'Purchase order {po_number} created.', 'success')
        return redirect(url_for('web_purchase_orders.list_orders'))
    except Exception as e:
        logger.exception('PO create error')
        flash(f'Could not create purchase order: {e}', 'danger')
        return redirect(url_for('web_purchase_orders.list_orders'))


@web_purchase_orders_bp.route('/<po_id>')
@jwt_required()
def view_order(po_id):
    user = _get_user()
    po = PurchaseOrderModel.find_by_id(po_id)
    if not po:
        flash('Purchase order not found.', 'danger')
        return redirect(url_for('web_purchase_orders.list_orders'))
    cid = _company_id()
    if str(po.get('company_id', '')) != str(cid):
        flash('Access denied.', 'danger')
        return redirect(url_for('web_purchase_orders.list_orders'))
    return render_template('purchase_orders/detail.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           order=PurchaseOrderModel.to_dict(po))