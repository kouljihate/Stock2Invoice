import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.purchase_order_model import PurchaseOrderModel
from app.core.models.supplier_model import SupplierModel
from app.core.utils.helpers import paginate

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


@web_purchase_orders_bp.route('/<po_id>')
@jwt_required()
def view_order(po_id):
    user = _get_user()
    po = PurchaseOrderModel.find_by_id(po_id)
    if not po:
        flash('Purchase order not found.', 'danger')
        return redirect(url_for('web_purchase_orders.list_orders'))
    return render_template('purchase_orders/detail.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           order=PurchaseOrderModel.to_dict(po))