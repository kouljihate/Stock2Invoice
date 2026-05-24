import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.goods_receipt_model import GoodsReceiptModel
from app.core.models.purchase_order_model import PurchaseOrderModel
from app.core.utils.helpers import paginate, oid
from app.core.services.event_service import EventService

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
        raw_pos = PurchaseOrderModel.find_all(1, 99999, {'company_id': oid(cid), 'status': 'sent'})[0] if cid else []

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
            'status': 'waiting',
            'company_id': oid(cid),
            'created_by': oid(get_jwt_identity()),
        }
        gr_id = GoodsReceiptModel.create(payload)
        user_obj = _get_user()
        EventService.record(cid, 'goods_receipt', gr_id, receipt_number, 'created', user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
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
        receipts = []
        for g in items:
            r = GoodsReceiptModel.to_dict(g)
            po_id = r.get('po_id')
            if po_id:
                po = PurchaseOrderModel.find_by_id(po_id)
                r['po_status'] = po.get('status', '') if po else ''
            else:
                r['po_status'] = ''
            receipts.append(r)
        return render_template('goods_receipt/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               receipts=receipts,
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Goods receipt list error')
        return render_template('goods_receipt/list.html', mode='web', receipts=[], total=0, page=1, per_page=20, pages=0)


@web_goods_receipt_bp.route('/<gr_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_receipt(gr_id):
    user = _get_user()
    cid = _company_id()
    gr = GoodsReceiptModel.find_by_id(gr_id)
    if not gr:
        flash('Goods receipt not found.', 'danger')
        return redirect(url_for('web_goods_receipt.list_receipts'))
    if str(gr.get('company_id', '')) != str(cid):
        flash('Access denied.', 'danger')
        return redirect(url_for('web_goods_receipt.list_receipts'))
    if request.method == 'GET':
        raw_pos = PurchaseOrderModel.find_all(1, 99999, {'company_id': oid(cid), 'status': 'sent'})[0] if cid else []
        pos = [{'id': str(p['_id']), 'po_number': p.get('po_number'), 'supplier_name': p.get('supplier_name', ''), 'supplier_id': str(p.get('supplier_id', '')) if p.get('supplier_id') else ''} for p in raw_pos]
        return render_template('goods_receipt/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               receipt=GoodsReceiptModel.to_dict(gr), pos=pos)
    try:
        data = request.form.to_dict(flat=False)
        items = []
        skus = data.get('sku', [])
        qtys = data.get('quantity', [])
        names = data.get('name', [])
        for i in range(len(skus)):
            if skus[i] and qtys[i] and int(qtys[i]) > 0:
                items.append({'sku': skus[i], 'quantity': int(qtys[i]),
                              'name': names[i] if i < len(names) else ''})
        payload = {
            'po_id': oid(request.form.get('po_id', '')),
            'po_number': request.form.get('po_number', ''),
            'supplier_id': oid(request.form.get('supplier_id', '')),
            'supplier_name': request.form.get('supplier_name', ''),
            'items': items,
            'notes': request.form.get('notes', ''),
        }
        GoodsReceiptModel.update(gr_id, payload)
        flash(f'Goods receipt updated.', 'success')
    except Exception as e:
        logger.exception('Goods receipt edit error')
        flash(f'Could not update goods receipt: {e}', 'danger')
    return redirect(url_for('web_goods_receipt.list_receipts'))


@web_goods_receipt_bp.route('/<gr_id>/mark-received', methods=['POST'])
@jwt_required()
def mark_po_received(gr_id):
    try:
        cid = _company_id()
        gr = GoodsReceiptModel.find_by_id(gr_id)
        if not gr:
            flash('Goods receipt not found.', 'danger')
            return redirect(url_for('web_goods_receipt.list_receipts'))
        if str(gr.get('company_id', '')) != str(cid):
            flash('Access denied.', 'danger')
            return redirect(url_for('web_goods_receipt.list_receipts'))
        po_id = str(gr.get('po_id', ''))
        if po_id:
            po = PurchaseOrderModel.find_by_id(po_id)
            if not po:
                flash('Linked purchase order not found.', 'danger')
                return redirect(url_for('web_goods_receipt.list_receipts'))
            PurchaseOrderModel.update(po_id, {'status': 'received'})
            GoodsReceiptModel.update(gr_id, {'status': 'received'})
            user_obj = _get_user()
            EventService.record(cid, 'purchase_order', po_id, po.get('po_number','') if po else '', 'received',
                                user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')

            # Build price lookup from PO items
            po_items = {it['sku']: it for it in (po.get('items') or [])}
            si_items = []
            for it in (gr.get('items') or []):
                sku = it.get('sku', '')
                po_it = po_items.get(sku, {})
                si_items.append({
                    'sku': sku,
                    'name': it.get('name', po_it.get('name', '')),
                    'quantity': int(it.get('quantity', 0)),
                    'unit_price': float(po_it.get('unit_price', 0)),
                })

            from datetime import datetime, timezone, timedelta
            from app.core.models.supplier_invoice_model import SupplierInvoiceModel
            count = SupplierInvoiceModel.count({'company_id': oid(cid)})
            inv_number = f"SI-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
            subtotal = sum(it['quantity'] * it['unit_price'] for it in si_items)
            discount_pct = float(po.get('discount_percent', 0))
            tax_pct = float(po.get('tax_percent', 0))
            discount = subtotal * discount_pct / 100
            taxable = subtotal - discount
            si_payload = {
                'invoice_number': inv_number,
                'supplier_id': oid(str(po.get('supplier_id', ''))),
                'supplier_name': po.get('supplier_name', ''),
                'po_id': oid(po_id),
                'po_number': po.get('po_number', ''),
                'invoice_date': datetime.now(timezone.utc),
                'due_date': datetime.now(timezone.utc) + timedelta(days=30),
                'items': si_items,
                'subtotal': subtotal,
                'discount_percent': discount_pct,
                'tax_percent': tax_pct,
                'discount_amount': discount,
                'tax_amount': taxable * tax_pct / 100,
                'total': taxable + (taxable * tax_pct / 100),
                'notes': f'Auto-generated from goods receipt {gr.get("receipt_number", "")}',
                'status': 'draft',
                'company_id': oid(cid),
                'created_by': oid(get_jwt_identity()),
            }
            si_payload['total'] = si_payload['subtotal'] - si_payload['discount_amount'] + si_payload['tax_amount']
            si_id = SupplierInvoiceModel.create(si_payload)
            EventService.record(cid, 'supplier_invoice', si_id, inv_number, 'created',
                                user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
            flash(f'Purchase order marked as received. Supplier invoice {inv_number} auto-generated.', 'success')
        else:
            flash('No linked purchase order.', 'warning')
    except Exception as e:
        logger.exception('Mark PO received error')
        flash(f'Could not mark PO as received: {e}', 'danger')
    return redirect(url_for('web_goods_receipt.list_receipts'))


@web_goods_receipt_bp.route('/<gr_id>/delete', methods=['POST'])
@jwt_required()
def delete_receipt(gr_id):
    try:
        cid = _company_id()
        gr = GoodsReceiptModel.find_by_id(gr_id)
        if not gr:
            flash('Goods receipt not found.', 'danger')
            return redirect(url_for('web_goods_receipt.list_receipts'))
        if str(gr.get('company_id', '')) != str(cid):
            flash('Access denied.', 'danger')
            return redirect(url_for('web_goods_receipt.list_receipts'))
        receipt_number = gr.get('receipt_number', '')
        GoodsReceiptModel.delete(gr_id)
        user_obj = _get_user()
        EventService.record(cid, 'goods_receipt', gr_id, receipt_number, 'deleted',
                            user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
        flash('Goods receipt deleted.', 'success')
    except Exception as e:
        logger.exception('Goods receipt delete error')
        flash(f'Could not delete goods receipt: {e}', 'danger')
    return redirect(url_for('web_goods_receipt.list_receipts'))