import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.customer_quote_model import CustomerQuoteModel
from app.core.utils.helpers import paginate

logger = logging.getLogger(__name__)
web_customer_quotes_bp = Blueprint('web_customer_quotes', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_customer_quotes_bp.route('')
@web_customer_quotes_bp.route('/')
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
        return render_template('customer_quotes/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               quotes=[CustomerQuoteModel.to_dict(q) for q in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Quote list error')
        return render_template('customer_quotes/list.html', mode='web', quotes=[], total=0, page=1, per_page=20, pages=0)


@web_customer_quotes_bp.route('/<quote_id>')
@jwt_required()
def view_quote(quote_id):
    user = _get_user()
    q = CustomerQuoteModel.find_by_id(quote_id)
    if not q:
        flash('Quote not found.', 'danger')
        return redirect(url_for('web_customer_quotes.list_quotes'))
    return render_template('customer_quotes/detail.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           quote=CustomerQuoteModel.to_dict(q))