import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.delivery_note_model import DeliveryNoteModel
from app.core.models.order_model import OrderModel
from app.core.utils.helpers import paginate, oid

logger = logging.getLogger(__name__)
web_delivery_notes_bp = Blueprint('web_delivery_notes', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_delivery_notes_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_delivery_note():
    user = _get_user()
    cid = _company_id()
    if request.method == 'GET':
        raw_orders = OrderModel.find_all(1, 99999, {'company_id': oid(cid)})[0] if cid else []
        orders = [{'id': str(o['_id']), 'order_number': o.get('order_number', ''), 'customer_name': o.get('customer_name', '')} for o in raw_orders]
        return render_template('delivery_notes/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               note=None, orders=orders)
    try:
        cid = _company_id()
        from datetime import datetime
        data = request.form.to_dict(flat=False)
        items = []
        skus = data.get('sku', [])
        qtys = data.get('quantity', [])
        names = data.get('name', [])
        for i in range(len(skus)):
            if skus[i] and qtys[i] and int(qtys[i]) > 0:
                items.append({'sku': skus[i], 'quantity': int(qtys[i]),
                              'name': names[i] if i < len(names) else ''})
        count = DeliveryNoteModel.count({'company_id': oid(cid)})
        dn_number = f"DN-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
        payload = {
            'dn_number': dn_number,
            'order_id': oid(request.form.get('order_id', '')),
            'order_number': request.form.get('order_number', ''),
            'customer_name': request.form.get('customer_name', ''),
            'items': items,
            'notes': request.form.get('notes', ''),
            'company_id': oid(cid),
            'created_by': oid(get_jwt_identity()),
        }
        DeliveryNoteModel.create(payload)
        flash(f'Delivery note {dn_number} created.', 'success')
        return redirect(url_for('web_delivery_notes.list_delivery_notes'))
    except Exception as e:
        logger.exception('Delivery note create error')
        flash(f'Could not create delivery note: {e}', 'danger')
        return redirect(url_for('web_delivery_notes.list_delivery_notes'))


@web_delivery_notes_bp.route('/<dn_id>/delete', methods=['POST'])
@jwt_required()
def delete_delivery_note(dn_id):
    dn = DeliveryNoteModel.find_by_id(dn_id)
    if not dn:
        flash('Delivery note not found.', 'danger')
    else:
        DeliveryNoteModel.delete(dn_id)
        flash('Delivery note deleted.', 'success')
    return redirect(url_for('web_delivery_notes.list_delivery_notes'))


@web_delivery_notes_bp.route('')
@web_delivery_notes_bp.route('/')
@jwt_required()
def list_delivery_notes():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = {'company_id': ObjectId(cid)} if cid else {}
        items, total = DeliveryNoteModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('delivery_notes/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               notes=[DeliveryNoteModel.to_dict(dn) for dn in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Delivery note list error')
        return render_template('delivery_notes/list.html', mode='web', notes=[], total=0, page=1, per_page=20, pages=0)