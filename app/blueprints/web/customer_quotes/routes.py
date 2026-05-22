import json
import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.customer_model import CustomerModel
from app.core.models.customer_quote_model import CustomerQuoteModel
from app.core.services.order_service import OrderService
from app.core.services.event_service import EventService
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
        customers = CustomerModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
        return render_template('customer_quotes/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               quote=None,
                               customers=[CustomerModel.to_dict(c) for c in customers])
    try:
        cid = _company_id()
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
            return redirect(url_for('web_customer_quotes.create_quote'))
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
        user_obj = UserModel.find_by_id(get_jwt_identity())
        EventService.record(cid, 'quote', str(payload.get('_id','')), quote_number, 'created',
                            user_id=get_jwt_identity(), user_name=user_obj.get('name','') if user_obj else '')
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


@web_customer_quotes_bp.route('/<quote_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_quote(quote_id):
    user = _get_user()
    quote = CustomerQuoteModel.find_by_id(quote_id)
    if not quote:
        flash('Quote not found.', 'danger')
        return redirect(url_for('web_customer_quotes.list_quotes'))
    cid = _company_id()
    if request.method == 'GET':
        customers = CustomerModel.find_all_unpaginated({'company_id': oid(cid)}) if cid else []
        return render_template('customer_quotes/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               quote=CustomerQuoteModel.to_dict(quote),
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
            return redirect(url_for('web_customer_quotes.edit_quote', quote_id=quote_id))
        valid_until_str = request.form.get('valid_until', '')
        valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d') if valid_until_str else None
        payload = {
            'customer_name': request.form.get('customer_name', ''),
            'customer_email': request.form.get('customer_email', ''),
            'customer_address': request.form.get('customer_address', ''),
            'items': items,
            'subtotal': sum(it['quantity'] * it['unit_price'] for it in items),
            'discount_percent': float(request.form.get('discount_percent', 0)),
            'tax_percent': float(request.form.get('tax_percent', 0)),
            'valid_until': valid_until,
            'notes': request.form.get('notes', ''),
            'status': request.form.get('status', 'draft'),
        }
        discount = payload['subtotal'] * payload['discount_percent'] / 100
        taxable = payload['subtotal'] - discount
        payload['discount_amount'] = discount
        payload['tax_amount'] = taxable * payload['tax_percent'] / 100
        payload['total'] = taxable + payload['tax_amount']
        CustomerQuoteModel.update(quote_id, payload)
        flash('Quote updated.', 'success')
        return redirect(url_for('web_customer_quotes.list_quotes'))
    except Exception as e:
        logger.exception('Quote edit error')
        flash(f'Could not update quote: {e}', 'danger')
        return redirect(url_for('web_customer_quotes.list_quotes'))


@web_customer_quotes_bp.route('/<quote_id>/send', methods=['POST'])
@jwt_required()
def send_quote(quote_id):
    quote = CustomerQuoteModel.find_by_id(quote_id)
    if not quote:
        flash('Quote not found.', 'danger')
        return redirect(url_for('web_customer_quotes.list_quotes'))
    try:
        CustomerQuoteModel.update(quote_id, {'status': 'sent'})
        cid = _company_id()
        user_id = get_jwt_identity()
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'quote', quote_id, quote.get('quote_number',''), 'sent',
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Quote sent to customer.', 'success')
    except Exception as e:
        logger.exception('Quote send error')
        flash(f'Could not send quote: {e}', 'danger')
    return redirect(url_for('web_customer_quotes.list_quotes'))


@web_customer_quotes_bp.route('/<quote_id>/validate', methods=['POST'])
@jwt_required()
def validate_quote(quote_id):
    quote = CustomerQuoteModel.find_by_id(quote_id)
    if not quote:
        flash('Quote not found.', 'danger')
        return redirect(url_for('web_customer_quotes.list_quotes'))
    try:
        cid = _company_id()
        user_id = get_jwt_identity()
        payload = {
            'customer_name': quote.get('customer_name', ''),
            'customer_email': quote.get('customer_email', ''),
            'customer_address': quote.get('customer_address', ''),
            'items': quote.get('items', []),
            'discount_percent': float(quote.get('discount_percent', 0)),
            'tax_percent': float(quote.get('tax_percent', 0)),
            'notes': f'From Quote {quote.get("quote_number", "")}',
            'status': 'confirmed',
        }
        order_id, order_number = OrderService.create(payload, user_id, cid)
        CustomerQuoteModel.update(quote_id, {
            'status': 'accepted',
            'generated_order_id': oid(order_id),
            'generated_order_number': order_number,
        })
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'quote', quote_id, quote.get('quote_number',''), 'validated',
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        EventService.record(cid, 'order', order_id, order_number, 'created',
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash(f'Quote converted to order {order_number}.', 'success')
        return redirect(url_for('web_orders.view_order', order_id=order_id))
    except Exception as e:
        logger.exception('Quote validate error')
        flash(f'Could not validate quote: {e}', 'danger')
        return redirect(url_for('web_customer_quotes.list_quotes'))


@web_customer_quotes_bp.route('/<quote_id>/delete', methods=['POST'])
@jwt_required()
def delete_quote(quote_id):
    quote = CustomerQuoteModel.find_by_id(quote_id)
    if not quote:
        flash('Quote not found.', 'danger')
    else:
        cid = _company_id()
        user_id = get_jwt_identity()
        user_obj = UserModel.find_by_id(user_id)
        CustomerQuoteModel.delete(quote_id)
        EventService.record(cid, 'quote', quote_id, quote.get('quote_number',''), 'deleted',
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Quote deleted.', 'success')
    return redirect(url_for('web_customer_quotes.list_quotes'))


@web_customer_quotes_bp.route('/ajax/create-customer', methods=['POST'])
@jwt_required()
def ajax_create_customer():
    try:
        cid = _company_id()
        data = {
            'type': request.form.get('type', 'prive'),
            'name': request.form.get('name', '').strip(),
            'contact': request.form.get('contact', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'address': request.form.get('address', '').strip(),
            'city': request.form.get('city', '').strip(),
            'ICE': request.form.get('ICE', '').strip(),
            'RC': request.form.get('RC', '').strip(),
            'paiement_terms': request.form.get('paiement_terms', '').strip(),
            'company_id': oid(cid),
        }
        if not data['name']:
            return jsonify({'ok': False, 'error': 'Customer name is required.'}), 400
        cid_str = CustomerModel.create(data)
        new_customer = CustomerModel.to_dict(CustomerModel.find_by_id(cid_str))
        return jsonify({'ok': True, 'customer': new_customer})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500