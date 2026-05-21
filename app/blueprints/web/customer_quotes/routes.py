import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.customer_quote_model import CustomerQuoteModel
from app.core.utils.helpers import paginate, oid

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


@web_customer_quotes_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_quote():
    user = _get_user()
    cid = _company_id()
    if request.method == 'GET':
        return render_template('customer_quotes/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               quote=None)
    try:
        cid = _company_id()
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
        count = CustomerQuoteModel.count({'company_id': oid(cid)})
        quote_number = f"Q-{datetime.now().strftime('%Y%m%d')}-{count + 1:04d}"
        valid_until_str = request.form.get('valid_until', '')
        valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d') if valid_until_str else None
        payload = {
            'quote_number': quote_number,
            'customer_name': request.form.get('customer_name', ''),
            'customer_email': request.form.get('customer_email', ''),
            'customer_address': request.form.get('customer_address', ''),
            'items': items,
            'subtotal': sum(it['quantity'] * it['unit_price'] for it in items),
            'discount_percent': float(request.form.get('discount_percent', 0)),
            'tax_percent': float(request.form.get('tax_percent', 0)),
            'valid_until': valid_until,
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
        CustomerQuoteModel.create(payload)
        flash(f'Quote {quote_number} created.', 'success')
        return redirect(url_for('web_customer_quotes.list_quotes'))
    except Exception as e:
        logger.exception('Quote create error')
        flash(f'Could not create quote: {e}', 'danger')
        return redirect(url_for('web_customer_quotes.list_quotes'))


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