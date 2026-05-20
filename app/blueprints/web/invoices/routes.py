import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.services.invoice_service import InvoiceService
from app.core.models.product_model import ProductModel
from app.core.models.user_model import UserModel
from app.core.utils.helpers import paginate, oid

logger = logging.getLogger(__name__)
web_invoices_bp = Blueprint('web_invoices', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_invoices_bp.route('')
@web_invoices_bp.route('/')
@jwt_required()
def list_invoices():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        filters = {}
        if request.args.get('status'):
            filters['status'] = request.args['status']
        cid = _company_id()
        items, total = InvoiceService.list(page, per_page, filters, cid)
        user = _get_user()
        return render_template('invoices/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               invoices=items, total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception as e:
        logger.exception('Invoice list error')
        flash('Could not load invoices.', 'danger')
        return render_template('invoices/list.html', mode='web',
                               invoices=[], total=0, page=1, per_page=20, pages=0)


@web_invoices_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_invoice():
    user = _get_user()
    cid = _company_id()
    if request.method == 'GET':
        products = ProductModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else ProductModel.find_all_unpaginated()
        return render_template('invoices/edit.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               invoice=None, products=products)

    try:
        data = request.form.to_dict(flat=False)
        items = []
        skus = data.get('sku', [])
        qtys = data.get('quantity', [])
        prices = data.get('unit_price', [])
        names = data.get('name', [])
        for i in range(len(skus)):
            if skus[i] and qtys[i] and int(qtys[i]) > 0:
                items.append({'sku': skus[i], 'quantity': qtys[i], 'unit_price': prices[i] if prices[i] else 0, 'name': names[i] if i < len(names) else ''})

        payload = {
            'customer_name': request.form.get('customer_name', ''),
            'customer_email': request.form.get('customer_email', ''),
            'customer_address': request.form.get('customer_address', ''),
            'items': items,
            'discount_percent': request.form.get('discount_percent', 0),
            'tax_percent': request.form.get('tax_percent', 10),
            'status': request.form.get('status', 'draft'),
            'notes': request.form.get('notes', ''),
        }

        errors = InvoiceService.validate(payload, cid)
        if errors:
            for e in errors:
                flash(e, 'danger')
            products = ProductModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else ProductModel.find_all_unpaginated()
            return render_template('invoices/edit.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None,
                                   invoice=payload, products=products)

        user_id = get_jwt_identity()
        invoice_id, invoice_number = InvoiceService.create(payload, user_id, cid)
        flash(f'Invoice {invoice_number} created.', 'success')
        return redirect(url_for('web_invoices.view_invoice', invoice_id=invoice_id))
    except Exception as e:
        logger.exception('Invoice create error')
        flash('Could not create invoice.', 'danger')
        products = ProductModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else ProductModel.find_all_unpaginated()
        return render_template('invoices/edit.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               invoice=request.form, products=products)


@web_invoices_bp.route('/<invoice_id>')
@jwt_required()
def view_invoice(invoice_id):
    user = _get_user()
    inv = InvoiceService.get_by_id(invoice_id)
    if not inv:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('web_invoices.list_invoices'))
    return render_template('invoices/detail.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           invoice=inv)


@web_invoices_bp.route('/<invoice_id>/print')
@jwt_required()
def print_invoice(invoice_id):
    user = _get_user()
    inv = InvoiceService.get_by_id(invoice_id)
    if not inv:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('web_invoices.list_invoices'))
    return render_template('invoices/print.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           invoice=inv)


@web_invoices_bp.route('/<invoice_id>/status', methods=['POST'])
@jwt_required()
def update_status(invoice_id):
    try:
        status = request.form.get('status')
        if status not in ('draft', 'sent', 'paid', 'cancelled'):
            flash('Invalid status.', 'danger')
            return redirect(url_for('web_invoices.view_invoice', invoice_id=invoice_id))
        user_id = get_jwt_identity()
        cid = _company_id()
        InvoiceService.update(invoice_id, {'status': status}, user_id, cid)
        flash('Invoice status updated.', 'success')
    except Exception as e:
        logger.exception('Invoice status update error')
        flash('Could not update status.', 'danger')
    return redirect(url_for('web_invoices.view_invoice', invoice_id=invoice_id))
