import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.goods_receipt_model import GoodsReceiptModel
from app.core.utils.helpers import paginate

logger = logging.getLogger(__name__)
web_goods_receipt_bp = Blueprint('web_goods_receipt', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


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