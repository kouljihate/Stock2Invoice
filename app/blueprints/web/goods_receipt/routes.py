import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.goods_receipt_model import GoodsReceiptModel
from app.core.models.purchase_order_model import PurchaseOrderModel
from app.core.utils.helpers import paginate, oid

logger = logging.getLogger(__name__)
web_goods_receipt_bp = Blueprint('web_goods_receipt', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_goods_receipt_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_receipt():
    user = _get_user()
    cid = _company_id()
    if request.method == 'GET':
        raw_pos = PurchaseOrderModel.find_all(1, 99999, {'company_id': oid(cid)})[0] if cid else []
        pos = [{'id': str(p['_id']), 'po_number': p.get('po_number'), 'supplier_name': p.get('supplier_name', ''), 'supplier_id': str(p.get('supplier_id', '')) if p.get('supplier_id') else ''} for p in raw_pos]
        return render_template('goods_receipt/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               receipt=None, pos=pos)
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
        count = GoodsReceiptModel.count({'company_id': oid(cid)})
        receipt_number = f"GR-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
        payload = {
            'receipt_number': receipt_number,
            'po_id': oid(request.form.get('po_id', '')),
            'po_number': request.form.get('po_number', ''),
            'supplier_id': oid(request.form.get('supplier_id', '')),
            'supplier_name': request.form.get('supplier_name', ''),
            'items': items,
            'notes': request.form.get('notes', ''),
            'company_id': oid(cid),
            'created_by': oid(get_jwt_identity()),
        }
        GoodsReceiptModel.create(payload)
        flash(f'Goods receipt {receipt_number} created.', 'success')
        return redirect(url_for('web_goods_receipt.list_receipts'))
    except Exception as e:
        logger.exception('Goods receipt create error')
        flash(f'Could not create goods receipt: {e}', 'danger')
        return redirect(url_for('web_goods_receipt.list_receipts'))


@web_goods_receipt_bp.route('')
@web_goods_receipt_bp.route('/')
@jwt_required()
def list_receipts():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = {'company_id': ObjectId(cid)} if cid else {}
        items, total = GoodsReceiptModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('goods_receipt/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               receipts=[GoodsReceiptModel.to_dict(g) for g in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Goods receipt list error')
        return render_template('goods_receipt/list.html', mode='web', receipts=[], total=0, page=1, per_page=20, pages=0)