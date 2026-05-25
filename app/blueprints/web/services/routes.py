import logging
from flask import Blueprint, render_template, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.customer_quote_model import CustomerQuoteModel
from app.core.models.order_model import CustomerOrderModel
from app.core.models.invoice_model import InvoiceModel
from app.core.utils.helpers import paginate

logger = logging.getLogger(__name__)
web_services_bp = Blueprint('web_services', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_services_bp.route('')
@web_services_bp.route('/')
@jwt_required()
def index():
    user = _get_user()
    return render_template('services/index.html', mode='web',
                           user=UserModel.to_dict(user) if user else None)


@web_services_bp.route('/quotes')
@jwt_required()
def list_quotes():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = {'company_id': ObjectId(cid)} if cid else {}
        if request.args.get('status'):
            filters['status'] = request.args['status']
        items, total = CustomerQuoteModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('services/quotes.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               quotes=[CustomerQuoteModel.to_dict(q) for q in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Service quotes list error')
        return render_template('services/quotes.html', mode='web', quotes=[], total=0, page=1, per_page=20, pages=0)


@web_services_bp.route('/orders')
@jwt_required()
def list_orders():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = {'company_id': ObjectId(cid)} if cid else {}
        if request.args.get('status'):
            filters['status'] = request.args['status']
        items, total = CustomerOrderModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('services/orders.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               orders=[CustomerOrderModel.to_dict(o) for o in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Service orders list error')
        return render_template('services/orders.html', mode='web', orders=[], total=0, page=1, per_page=20, pages=0)


@web_services_bp.route('/invoices')
@jwt_required()
def list_invoices():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = {'company_id': ObjectId(cid)} if cid else {}
        if request.args.get('status'):
            filters['status'] = request.args['status']
        items, total = InvoiceModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('services/invoices.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               invoices=[InvoiceModel.to_dict(i) for i in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Service invoices list error')
        return render_template('services/invoices.html', mode='web', invoices=[], total=0, page=1, per_page=20, pages=0)