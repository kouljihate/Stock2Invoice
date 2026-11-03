import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.models.user_model import UserModel
from app.core.models.payment_model import PaymentModel
from app.core.models.supplier_model import SupplierModel
from app.core.utils.helpers import paginate, oid, tenant_filter
from app.core.services.event_service import EventService
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)
web_payments_bp = Blueprint('web_payments', __name__, template_folder='../../../templates')


def _get_user():
    """Acting user document, resolved from the database (never claims)."""
    from app.core.utils.context import current_user
    return current_user()


def _company_id():
    """Acting user's company id, resolved from the database (never claims)."""
    from app.core.utils.context import current_company_id
    return current_company_id()


@web_payments_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_payment():
    user = _get_user()
    cid = _company_id()
    if request.method == 'GET':
        suppliers = SupplierModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
        return render_template('payments/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               payment=None, suppliers=suppliers)
    try:
        cid = _company_id()
        from datetime import datetime
        count = PaymentModel.count({'company_id': oid(cid)})
        payment_number = f"PMT-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
        payment_date_str = request.form.get('payment_date', '')
        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d') if payment_date_str else None
        payload = {
            'payment_number': payment_number,
            'supplier_id': oid(request.form.get('supplier_id', '')),
            'supplier_name': request.form.get('supplier_name', ''),
            'invoice_id': oid(request.form.get('invoice_id', '')),
            'invoice_number': request.form.get('invoice_number', ''),
            'amount': float(request.form.get('amount', 0)),
            'payment_date': payment_date,
            'payment_method': request.form.get('payment_method', ''),
            'reference': request.form.get('reference', ''),
            'notes': request.form.get('notes', ''),
            'status': 'pending',
            'company_id': oid(cid),
            'created_by': oid(get_jwt_identity()),
        }
        pmt_id = PaymentModel.create(payload)
        user_obj = _get_user()
        EventService.record(cid, 'payment', pmt_id, payment_number, 'created', user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
        flash(f'Payment {payment_number} created.', 'success')
        return redirect(url_for('web_payments.list_payments'))
    except Exception as e:
        logger.exception('Payment create error')
        flash(f'Could not create payment: {e}', 'danger')
        return redirect(url_for('web_payments.list_payments'))


@web_payments_bp.route('')
@web_payments_bp.route('/')
@jwt_required()
def list_payments():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = tenant_filter(cid)
        items, total = PaymentModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('payments/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               payments=[PaymentModel.to_dict(p) for p in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Payment list error')
        return render_template('payments/list.html', mode='web', payments=[], total=0, page=1, per_page=20, pages=0)