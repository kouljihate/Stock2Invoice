import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.purchase_order_model import PurchaseOrderModel
from app.core.models.supplier_model import SupplierModel
from app.core.utils.helpers import paginate, oid
from app.core.services.event_service import EventService

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
        po_id = PurchaseOrderModel.create(payload)
        user_obj = _get_user()
        EventService.record(cid, 'purchase_order', po_id, po_number, 'created', user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
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


@web_purchase_orders_bp.route('/<po_id>/send', methods=['POST'])
@jwt_required()
def send_order(po_id):
    try:
        cid = _company_id()
        po = PurchaseOrderModel.find_by_id(po_id)
        if not po:
            flash('Purchase order not found.', 'danger')
            return redirect(url_for('web_purchase_orders.list_orders'))
        if str(po.get('company_id', '')) != str(cid):
            flash('Access denied.', 'danger')
            return redirect(url_for('web_purchase_orders.list_orders'))
        PurchaseOrderModel.update(po_id, {'status': 'sent'})
        user_obj = _get_user()
        EventService.record(cid, 'purchase_order', po_id, po.get('po_number',''), 'sent',
                            user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')

        # Auto-generate Goods Receipt with status 'waiting'
        from datetime import datetime
        from app.core.models.goods_receipt_model import GoodsReceiptModel
        gr_count = GoodsReceiptModel.count({'company_id': oid(cid)})
        receipt_number = f"GR-{datetime.now().strftime('%Y%m%d')}-{gr_count + 1:04d}"
        po_items = po.get('items', [])
        gr_items = [{'sku': it.get('sku',''), 'name': it.get('name',''), 'quantity': it.get('quantity', 0)} for it in po_items]
        gr_payload = {
            'receipt_number': receipt_number,
            'po_id': oid(po_id),
            'po_number': po.get('po_number', ''),
            'supplier_id': oid(str(po.get('supplier_id', ''))) if po.get('supplier_id') else None,
            'supplier_name': po.get('supplier_name', ''),
            'items': gr_items,
            'notes': f'Auto-generated from PO {po.get("po_number", "")}',
            'status': 'waiting',
            'company_id': oid(cid),
            'created_by': oid(get_jwt_identity()),
        }
        GoodsReceiptModel.create(gr_payload)
        flash(f'Purchase order sent. Goods receipt {receipt_number} auto-generated with status waiting.', 'success')
    except Exception as e:
        logger.exception('PO send error')
        flash(f'Could not send purchase order: {e}', 'danger')
    return redirect(url_for('web_purchase_orders.list_orders'))


@web_purchase_orders_bp.route('/<po_id>/delete', methods=['POST'])
@jwt_required()
def delete_order(po_id):
    try:
        cid = _company_id()
        po = PurchaseOrderModel.find_by_id(po_id)
        if not po:
            flash('Purchase order not found.', 'danger')
            return redirect(url_for('web_purchase_orders.list_orders'))
        if str(po.get('company_id', '')) != str(cid):
            flash('Access denied.', 'danger')
            return redirect(url_for('web_purchase_orders.list_orders'))
        PurchaseOrderModel.delete(po_id)
        user_obj = _get_user()
        EventService.record(cid, 'purchase_order', po_id, po.get('po_number',''), 'deleted',
                            user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
        flash('Purchase order deleted.', 'success')
    except Exception as e:
        logger.exception('PO delete error')
        flash(f'Could not delete purchase order: {e}', 'danger')
    return redirect(url_for('web_purchase_orders.list_orders'))