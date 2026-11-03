import logging
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.services.invoice_service import InvoiceService
from app.core.services.pdf_service import generate_invoice_pdf
from app.core.models.invoice_model import InvoiceModel
from app.core.models.product_model import ProductModel
from app.core.models.customer_model import CustomerModel
from app.core.models.user_model import UserModel
from app.core.models.company_model import CompanyModel
from app.core.services.event_service import EventService
from app.core.utils.helpers import paginate, oid, tenant_filter

logger = logging.getLogger(__name__)
web_invoices_bp = Blueprint('web_invoices', __name__, template_folder='../../../templates')


def _get_user():
    """Acting user document, resolved from the database (never claims)."""
    from app.core.utils.context import current_user
    return current_user()


def _company_id():
    """Acting user's company id, resolved from the database (never claims)."""
    from app.core.utils.context import current_company_id
    return current_company_id()


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
        customers = CustomerModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
        products = ProductModel.find_all_unpaginated(tenant_filter(cid))
        return render_template('invoices/edit.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               invoice=None, products=products,
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
            return redirect(url_for('web_invoices.create_invoice'))

        payload = {
            'customer_name': request.form.get('customer_name', ''),
            'contact_name': request.form.get('contact_name', ''),
            'contact_email': request.form.get('contact_email', ''),
            'customer_address': request.form.get('customer_address', ''),
            'customer_city': request.form.get('customer_city', ''),
            'customer_country': request.form.get('customer_country', ''),
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
            customers = CustomerModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
            products = ProductModel.find_all_unpaginated(tenant_filter(cid))
            return render_template('invoices/edit.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None,
                                   invoice=payload, products=products,
                                   customers=[CustomerModel.to_dict(c) for c in customers])

        user_id = get_jwt_identity()
        invoice_id, invoice_number = InvoiceService.create(payload, user_id, cid)
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'invoice', invoice_id, invoice_number, 'created', user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash(f'Invoice {invoice_number} created.', 'success')
        return redirect(url_for('web_invoices.view_invoice', invoice_id=invoice_id))
    except Exception as e:
        logger.exception('Invoice create error')
        flash('Could not create invoice.', 'danger')
        customers = CustomerModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
        products = ProductModel.find_all_unpaginated(tenant_filter(cid))
        return render_template('invoices/edit.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               invoice=request.form, products=products,
                               customers=[CustomerModel.to_dict(c) for c in customers])


@web_invoices_bp.route('/<invoice_id>')
@jwt_required()
def view_invoice(invoice_id):
    user = _get_user()
    cid = _company_id()
    inv = InvoiceService.get_by_id(invoice_id, cid)
    if not inv:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('web_invoices.list_invoices'))
    return render_template('invoices/detail.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           invoice=inv)


@web_invoices_bp.route('/<invoice_id>/delete', methods=['POST'])
@jwt_required()
def delete_invoice(invoice_id):
    inv = InvoiceModel.find_by_id(invoice_id)
    if not inv:
        flash('Invoice not found.', 'danger')
    else:
        cid = _company_id()
        if str(inv.get('company_id', '')) != str(cid):
            flash('Access denied.', 'danger')
            return redirect(url_for('web_invoices.list_invoices'))
        user_id = get_jwt_identity()
        user_obj = UserModel.find_by_id(user_id)
        inv_number = inv.get('invoice_number', '')
        InvoiceModel.delete(invoice_id)
        EventService.record(cid, 'invoice', invoice_id, inv_number, 'deleted', user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Invoice deleted.', 'success')
    return redirect(url_for('web_invoices.list_invoices'))


@web_invoices_bp.route('/<invoice_id>/print')
@jwt_required()
def print_invoice(invoice_id):
    user = _get_user()
    cid = _company_id()
    inv = InvoiceService.get_by_id(invoice_id, cid)
    if not inv:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('web_invoices.list_invoices'))
    return render_template('invoices/print.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           invoice=inv)


@web_invoices_bp.route('/<invoice_id>/pdf')
@jwt_required()
def download_pdf(invoice_id):
    cid = _company_id()
    inv = InvoiceService.get_by_id(invoice_id, cid)
    if not inv:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('web_invoices.list_invoices'))
    company = None
    if cid:
        company = CompanyModel.find_by_id(cid)
        if company:
            company = CompanyModel.to_dict(company)
    buf = generate_invoice_pdf(inv, company)
    inv_number = inv.get('invoice_number', 'invoice')
    safe_name = inv_number.replace('/', '_').replace('\\', '_')
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=False,
                     download_name=f'{safe_name}.pdf')


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
        inv = InvoiceService.get_by_id(invoice_id, cid)
        old_status = inv.get('status') if inv else ''
        InvoiceService.update(invoice_id, {'status': status}, user_id, cid)
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'invoice', invoice_id, inv.get('invoice_number','') if inv else '', 'status_changed',
                            changes={'from': old_status, 'to': status},
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Invoice status updated.', 'success')
    except Exception as e:
        logger.exception('Invoice status update error')
        flash('Could not update status.', 'danger')
    return redirect(url_for('web_invoices.view_invoice', invoice_id=invoice_id))
