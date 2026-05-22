import logging
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.user_model import UserModel
from app.core.models.customer_model import CustomerModel
from app.core.services.event_service import EventService
from app.core.utils.helpers import paginate

logger = logging.getLogger(__name__)
web_customers_bp = Blueprint('web_customers', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_customers_bp.route('')
@web_customers_bp.route('/')
@jwt_required()
def list_customers():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = {'company_id': ObjectId(cid)} if cid else {}
        items, total = CustomerModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('customers/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               customers=[CustomerModel.to_dict(c) for c in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Customer list error')
        return render_template('customers/list.html', mode='web', customers=[], total=0, page=1, per_page=20, pages=0)


@web_customers_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_customer():
    user = _get_user()
    if request.method == 'GET':
        return render_template('customers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None, customer=None)
    try:
        cid = _company_id()
        from bson.objectid import ObjectId
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
            'company_id': ObjectId(cid),
        }
        if not data['name']:
            flash('Customer name is required.', 'danger')
            return render_template('customers/form.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None, customer=request.form)
        CustomerModel.create(data)
        user_id = get_jwt_identity()
        cid = _company_id()
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'customer', '', data.get('name',''), 'created',
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Customer created.', 'success')
        return redirect(url_for('web_customers.list_customers'))
    except Exception as e:
        logger.exception('Customer create error')
        flash(f'Could not create customer: {e}', 'danger')
        return render_template('customers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None, customer=request.form)


@web_customers_bp.route('/bulk-upload', methods=['GET', 'POST'])
@jwt_required()
def bulk_upload():
    user = _get_user()
    cid = _company_id()

    if request.method == 'GET':
        return render_template('customers/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=None)

    json_data = request.form.get('json_data')
    if json_data:
        rows = json.loads(json_data)
        from bson.objectid import ObjectId
        results = []
        success_count = 0
        for idx, row in enumerate(rows):
            entry = {'row': idx + 1, 'name': row.get('name', ''), 'errors': [], 'status': ''}
            if not row.get('name', '').strip():
                entry['errors'] = ['Customer name is required.']
                entry['status'] = 'error'
                results.append(entry)
                continue
            data = {
                'type': row.get('type', 'prive'),
                'name': row.get('name', '').strip(),
                'contact': row.get('contact', '').strip(),
                'email': row.get('email', '').strip(),
                'phone': row.get('phone', '').strip(),
                'address': row.get('address', '').strip(),
                'city': row.get('city', '').strip(),
                'ICE': row.get('ICE', '').strip(),
                'RC': row.get('RC', '').strip(),
                'paiement_terms': row.get('paiement_terms', '').strip(),
                'company_id': ObjectId(cid),
            }
            try:
                CustomerModel.create(data)
                entry['status'] = 'success'
                success_count += 1
            except Exception as e:
                entry['errors'] = [str(e)]
                entry['status'] = 'error'
            results.append(entry)
        flash(f'{success_count} of {len(rows)} customers imported successfully.', 'success')
        return render_template('customers/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=results)

    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return render_template('customers/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=None)

    file = request.files['file']
    if not file.filename:
        flash('No file selected.', 'danger')
        return render_template('customers/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=None)

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    rows = []
    if ext == 'json':
        try:
            raw = json.load(file.stream)
            rows = raw if isinstance(raw, list) else [raw]
        except Exception as e:
            flash(f'Invalid JSON file: {e}', 'danger')
            return render_template('customers/bulk_upload.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None,
                                   preview=None, results=None)
    elif ext == 'csv':
        import csv, io
        try:
            text = io.StringIO(file.stream.read().decode('utf-8-sig'))
            reader = csv.DictReader(text)
            rows = [r for r in reader if any(v.strip() for v in r.values())]
            if not rows:
                flash('CSV file is empty.', 'danger')
                return render_template('customers/bulk_upload.html', mode='web',
                                       user=UserModel.to_dict(user) if user else None,
                                       preview=None, results=None)
        except Exception as e:
            flash(f'Invalid CSV file: {e}', 'danger')
            return render_template('customers/bulk_upload.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None,
                                   preview=None, results=None)
    else:
        flash('Unsupported format. Please upload a JSON or CSV file.', 'danger')
        return render_template('customers/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=None)

    HEADER_MAP = {
        'type': 'type', 'name': 'name', 'contact': 'contact', 'email': 'email',
        'phone': 'phone', 'city': 'city', 'paiement_terms': 'paiement_terms',
        'paiement terms': 'paiement_terms', 'payment terms': 'paiement_terms',
        'address': 'address', 'ice': 'ICE', 'rc': 'RC',
    }
    cleaned = []
    for row in rows:
        r = {}
        for csv_key, val in row.items():
            key = csv_key.strip().lower()
            mapped = HEADER_MAP.get(key, key)
            r[mapped] = val.strip() if isinstance(val, str) else val
        cleaned.append({
            'type': r.get('type', 'prive'),
            'name': r.get('name', ''),
            'contact': r.get('contact', ''),
            'email': r.get('email', ''),
            'phone': r.get('phone', ''),
            'address': r.get('address', ''),
            'city': r.get('city', ''),
            'paiement_terms': r.get('paiement_terms', ''),
            'ICE': r.get('ICE', ''),
            'RC': r.get('RC', ''),
        })

    return render_template('customers/bulk_upload.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           preview=cleaned, results=None)


@web_customers_bp.route('/<customer_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_customer(customer_id):
    user = _get_user()
    customer = CustomerModel.find_by_id(customer_id)
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('web_customers.list_customers'))
    if request.method == 'GET':
        return render_template('customers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               customer=CustomerModel.to_dict(customer))
    try:
        data = {'type': request.form.get('type', 'prive')}
        for k in ('name', 'contact', 'email', 'phone', 'address', 'city'):
            data[k] = request.form.get(k, '').strip()
        data['ICE'] = request.form.get('ICE', '').strip()
        data['RC'] = request.form.get('RC', '').strip()
        data['paiement_terms'] = request.form.get('paiement_terms', '').strip()
        if not data['name']:
            flash('Customer name is required.', 'danger')
            return render_template('customers/form.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None, customer=request.form)
        CustomerModel.update(customer_id, data)
        user_id = get_jwt_identity()
        cid = _company_id()
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'customer', customer_id, data.get('name',''), 'updated',
                            changes={'field': 'details', 'old_value': '', 'new_value': 'updated'},
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Customer updated.', 'success')
        return redirect(url_for('web_customers.list_customers'))
    except Exception as e:
        logger.exception('Customer edit error')
        flash(f'Could not update customer: {e}', 'danger')
        return render_template('customers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None, customer=request.form)


@web_customers_bp.route('/<customer_id>/delete', methods=['POST'])
@jwt_required()
def delete_customer(customer_id):
    customer = CustomerModel.find_by_id(customer_id)
    if not customer:
        flash('Customer not found.', 'danger')
    else:
        cid = _company_id()
        user_id = get_jwt_identity()
        user_obj = UserModel.find_by_id(user_id)
        CustomerModel.delete(customer_id)
        EventService.record(cid, 'customer', customer_id, customer.get('name',''), 'deleted',
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Customer deleted.', 'success')
    return redirect(url_for('web_customers.list_customers'))
