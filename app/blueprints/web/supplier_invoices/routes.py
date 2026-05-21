import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.supplier_invoice_model import SupplierInvoiceModel
from app.core.utils.helpers import paginate

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


@web_supplier_invoices_bp.route('/<inv_id>')
@jwt_required()
def view_invoice(inv_id):
    user = _get_user()
    inv = SupplierInvoiceModel.find_by_id(inv_id)
    if not inv:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('web_supplier_invoices.list_invoices'))
    return render_template('supplier_invoices/detail.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           invoice=SupplierInvoiceModel.to_dict(inv))