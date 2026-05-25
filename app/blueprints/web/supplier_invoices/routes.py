import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.supplier_invoice_model import SupplierInvoiceModel
from app.core.models.supplier_model import SupplierModel
from app.core.utils.helpers import paginate, oid
from app.core.services.event_service import EventService

logger = logging.getLogger(__name__)
web_supplier_invoices_bp = Blueprint('web_supplier_invoices', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_supplier_invoices_bp.route('')
@web_supplier_invoices_bp.route('/')
@jwt_required()
def list_invoices():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = {'company_id': ObjectId(cid)} if cid else {}
        if request.args.get('status'):
            filters['status'] = request.args['status']
        items, total = SupplierInvoiceModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('supplier_invoices/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               invoices=[SupplierInvoiceModel.to_dict(i) for i in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Supplier invoice list error')
        return render_template('supplier_invoices/list.html', mode='web', invoices=[], total=0, page=1, per_page=20, pages=0)


@web_supplier_invoices_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_invoice():
    user = _get_user()
    cid = _company_id()
    if request.method == 'GET':
        suppliers = SupplierModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
        return render_template('supplier_invoices/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               invoice=None, suppliers=suppliers)
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
        count = SupplierInvoiceModel.count({'company_id': oid(cid)})
        inv_number = f"SI-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
        due_date_str = request.form.get('due_date', '')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        payload = {
            'invoice_number': inv_number,
            'supplier_id': oid(request.form.get('supplier_id', '')),
            'supplier_name': request.form.get('supplier_name', ''),
            'po_id': oid(request.form.get('po_id', '')),
            'po_number': request.form.get('po_number', ''),
            'invoice_date': datetime.now(timezone.utc),
            'due_date': due_date,
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
        inv_id = SupplierInvoiceModel.create(payload)
        user_obj = _get_user()
        EventService.record(cid, 'supplier_invoice', inv_id, inv_number, 'created', user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
        flash(f'Supplier invoice {inv_number} created.', 'success')
        return redirect(url_for('web_supplier_invoices.list_invoices'))
    except Exception as e:
        logger.exception('Supplier invoice create error')
        flash(f'Could not create supplier invoice: {e}', 'danger')
        return redirect(url_for('web_supplier_invoices.list_invoices'))


@web_supplier_invoices_bp.route('/<inv_id>')
@jwt_required()
def view_invoice(inv_id):
    user = _get_user()
    inv = SupplierInvoiceModel.find_by_id(inv_id)
    if not inv:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('web_supplier_invoices.list_invoices'))
    cid = _company_id()
    if str(inv.get('company_id', '')) != str(cid):
        flash('Access denied.', 'danger')
        return redirect(url_for('web_supplier_invoices.list_invoices'))
    return render_template('supplier_invoices/detail.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           invoice=SupplierInvoiceModel.to_dict(inv))


@web_supplier_invoices_bp.route('/<inv_id>/validate', methods=['POST'])
@jwt_required()
def validate_invoice(inv_id):
    try:
        cid = _company_id()
        inv = SupplierInvoiceModel.find_by_id(inv_id)
        if not inv:
            flash('Supplier invoice not found.', 'danger')
            return redirect(url_for('web_supplier_invoices.list_invoices'))
        if str(inv.get('company_id', '')) != str(cid):
            flash('Access denied.', 'danger')
            return redirect(url_for('web_supplier_invoices.list_invoices'))
        
        # Update invoice status to approved
        SupplierInvoiceModel.update(inv_id, {'status': 'approved'})
        
        # Create payment record
        from app.core.models.payment_model import PaymentModel
        from app.core.models.supplier_model import SupplierModel
        
        supplier = SupplierModel.find_by_id(inv.get('supplier_id'))
        payment_data = {
            'payment_number': f"PAY-{datetime.now().strftime('%Y%m%d')}-{PaymentModel.count() + 1:04d}",
            'supplier_id': inv.get('supplier_id'),
            'supplier_name': inv.get('supplier_name', ''),
            'invoice_id': inv_id,
            'invoice_number': inv.get('invoice_number', ''),
            'amount': inv.get('total', 0),
            'payment_date': datetime.now(timezone.utc),
            'payment_method': 'bank_transfer',  # Default method
            'reference': f'Payment for invoice {inv.get("invoice_number")}',
            'notes': f'Auto-generated payment for validated supplier invoice {inv.get("invoice_number")}',
            'status': 'pending',  # Payment starts as pending, to be marked as paid when actually paid
            'company_id': inv.get('company_id'),
            'created_by': get_jwt_identity()
        }
        PaymentModel.create(payment_data)
        
        user_obj = _get_user()
        EventService.record(cid, 'supplier_invoice', inv_id, inv.get('invoice_number',''), 'approved',
                            user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
        flash('Supplier invoice validated and payment created.', 'success')
    except Exception as e:
        logger.exception('Supplier invoice validate error')
        flash(f'Could not validate supplier invoice: {e}', 'danger')
    return redirect(url_for('web_supplier_invoices.list_invoices'))


@web_supplier_invoices_bp.route('/<inv_id>/invalidate', methods=['POST'])
@jwt_required()
def invalidate_invoice(inv_id):
    try:
        cid = _company_id()
        inv = SupplierInvoiceModel.find_by_id(inv_id)
        if not inv:
            flash('Supplier invoice not found.', 'danger')
            return redirect(url_for('web_supplier_invoices.list_invoices'))
        if str(inv.get('company_id', '')) != str(cid):
            flash('Access denied.', 'danger')
            return redirect(url_for('web_supplier_invoices.list_invoices'))
        SupplierInvoiceModel.update(inv_id, {'status': 'draft'})
        user_obj = _get_user()
        EventService.record(cid, 'supplier_invoice', inv_id, inv.get('invoice_number',''), 'invalidated',
                            user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
        flash('Supplier invoice invalidated.', 'success')
    except Exception as e:
        logger.exception('Supplier invoice invalidate error')
        flash(f'Could not invalidate supplier invoice: {e}', 'danger')
    return redirect(url_for('web_supplier_invoices.list_invoices'))


@web_supplier_invoices_bp.route('/<inv_id>/delete', methods=['POST'])
@jwt_required()
def delete_invoice(inv_id):
    try:
        cid = _company_id()
        inv = SupplierInvoiceModel.find_by_id(inv_id)
        if not inv:
            flash('Supplier invoice not found.', 'danger')
            return redirect(url_for('web_supplier_invoices.list_invoices'))
        if str(inv.get('company_id', '')) != str(cid):
            flash('Access denied.', 'danger')
            return redirect(url_for('web_supplier_invoices.list_invoices'))
        SupplierInvoiceModel.delete(inv_id)
        user_obj = _get_user()
        EventService.record(cid, 'supplier_invoice', inv_id, inv.get('invoice_number',''), 'deleted',
                            user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
        flash('Supplier invoice deleted.', 'success')
    except Exception as e:
        logger.exception('Supplier invoice delete error')
        flash(f'Could not delete supplier invoice: {e}', 'danger')
    return redirect(url_for('web_supplier_invoices.list_invoices'))