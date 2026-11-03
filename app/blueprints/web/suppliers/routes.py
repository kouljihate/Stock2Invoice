import logging
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.core.models.user_model import UserModel
from app.core.models.supplier_model import SupplierModel
from app.core.services.event_service import EventService
from app.core.utils.helpers import paginate, tenant_filter

logger = logging.getLogger(__name__)
web_suppliers_bp = Blueprint('web_suppliers', __name__, template_folder='../../../templates')


def _get_user():
    """Acting user document, resolved from the database (never claims)."""
    from app.core.utils.context import current_user
    return current_user()


def _company_id():
    """Acting user's company id, resolved from the database (never claims)."""
    from app.core.utils.context import current_company_id
    return current_company_id()


@web_suppliers_bp.route('')
@web_suppliers_bp.route('/')
@jwt_required()
def list_suppliers():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        cid = _company_id()
        from bson.objectid import ObjectId
        filters = tenant_filter(cid)
        items, total = SupplierModel.find_all(page, per_page, filters)
        user = _get_user()
        return render_template('suppliers/list.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               suppliers=[SupplierModel.to_dict(s) for s in items],
                               total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception:
        logger.exception('Supplier list error')
        return render_template('suppliers/list.html', mode='web', suppliers=[], total=0, page=1, per_page=20, pages=0)


@web_suppliers_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_supplier():
    user = _get_user()
    if request.method == 'GET':
        return render_template('suppliers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None, supplier=None)
    try:
        cid = _company_id()
        from bson.objectid import ObjectId
        data = {
            'name': request.form.get('name', '').strip(),
            'contact_name': request.form.get('contact_name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'address': request.form.get('address', '').strip(),
            'city': request.form.get('city', '').strip(),
            'ice': request.form.get('ice', '').strip(),
            'rc': request.form.get('rc', '').strip(),
            'payment_terms': request.form.get('payment_terms', '').strip(),
            'company_id': ObjectId(cid),
        }
        if not data['name']:
            flash('Supplier name is required.', 'danger')
            return render_template('suppliers/form.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None, supplier=request.form)
        SupplierModel.create(data)
        user_id = get_jwt_identity()
        cid = _company_id()
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'supplier', '', data.get('name',''), 'created',
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Supplier created.', 'success')
        return redirect(url_for('web_suppliers.list_suppliers'))
    except Exception as e:
        logger.exception('Supplier create error')
        flash(f'Could not create supplier: {e}', 'danger')
        return render_template('suppliers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None, supplier=request.form)


@web_suppliers_bp.route('/bulk-upload', methods=['GET', 'POST'])
@jwt_required()
def bulk_upload():
    user = _get_user()
    cid = _company_id()

    if request.method == 'GET':
        return render_template('suppliers/bulk_upload.html', mode='web',
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
                entry['errors'] = ['Supplier name is required.']
                entry['status'] = 'error'
                results.append(entry)
                continue
            data = {
                'name': row.get('name', '').strip(),
                'contact_name': row.get('contact_name', '').strip(),
                'email': row.get('email', '').strip(),
                'phone': row.get('phone', '').strip(),
                'address': row.get('address', '').strip(),
                'city': row.get('city', '').strip(),
                'ice': row.get('ice', '').strip(),
                'rc': row.get('rc', '').strip(),
                'payment_terms': row.get('payment_terms', '').strip(),
                'company_id': ObjectId(cid),
            }
            try:
                SupplierModel.create(data)
                entry['status'] = 'success'
                success_count += 1
            except Exception as e:
                entry['errors'] = [str(e)]
                entry['status'] = 'error'
            results.append(entry)
        flash(f'{success_count} of {len(rows)} suppliers imported successfully.', 'success')
        return render_template('suppliers/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=results)

    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return render_template('suppliers/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=None)

    file = request.files['file']
    if not file.filename:
        flash('No file selected.', 'danger')
        return render_template('suppliers/bulk_upload.html', mode='web',
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
            return render_template('suppliers/bulk_upload.html', mode='web',
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
                return render_template('suppliers/bulk_upload.html', mode='web',
                                       user=UserModel.to_dict(user) if user else None,
                                       preview=None, results=None)
        except Exception as e:
            flash(f'Invalid CSV file: {e}', 'danger')
            return render_template('suppliers/bulk_upload.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None,
                                   preview=None, results=None)
    else:
        flash('Unsupported format. Please upload a JSON or CSV file.', 'danger')
        return render_template('suppliers/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=None)

    cleaned = []
    HEADER_MAP = {
        'name': 'name', 'contact': 'contact_name', 'email': 'email',
        'phone': 'phone', 'city': 'city', 'payment_terms': 'payment_terms',
        'payment terms': 'payment_terms', 'address': 'address',
        'ice': 'ice', 'rc': 'rc',
    }
    for row in rows:
        r = {}
        for csv_key, val in row.items():
            key = csv_key.strip().lower()
            mapped = HEADER_MAP.get(key, key)
            r[mapped] = val.strip() if isinstance(val, str) else val
        cleaned.append({
            'name': r.get('name', ''),
            'contact_name': r.get('contact_name', ''),
            'email': r.get('email', ''),
            'phone': r.get('phone', ''),
            'address': r.get('address', ''),
            'city': r.get('city', ''),
            'ice': r.get('ice', ''),
            'rc': r.get('rc', ''),
            'payment_terms': r.get('payment_terms', ''),
        })

    return render_template('suppliers/bulk_upload.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           preview=cleaned, results=None)


@web_suppliers_bp.route('/<supplier_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_supplier(supplier_id):
    user = _get_user()
    supplier = SupplierModel.find_by_id(supplier_id)
    if not supplier:
        flash('Supplier not found.', 'danger')
        return redirect(url_for('web_suppliers.list_suppliers'))
    cid = _company_id()
    if str(supplier.get('company_id', '')) != str(cid):
        flash('Access denied.', 'danger')
        return redirect(url_for('web_suppliers.list_suppliers'))
    if request.method == 'GET':
        return render_template('suppliers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               supplier=SupplierModel.to_dict(supplier))
    try:
        data = {k: request.form.get(k, '').strip() for k in ('name', 'contact_name', 'email', 'phone', 'address', 'city', 'ice', 'rc', 'payment_terms')}
        if not data['name']:
            flash('Supplier name is required.', 'danger')
            return render_template('suppliers/form.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None, supplier=request.form)
        SupplierModel.update(supplier_id, data)
        user_id = get_jwt_identity()
        cid = _company_id()
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'supplier', supplier_id, data.get('name',''), 'updated',
                            changes={'field': 'details', 'old_value': '', 'new_value': 'updated'},
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Supplier updated.', 'success')
        return redirect(url_for('web_suppliers.list_suppliers'))
    except Exception as e:
        logger.exception('Supplier edit error')
        flash(f'Could not update supplier: {e}', 'danger')
        return render_template('suppliers/form.html', mode='web',
                               user=UserModel.to_dict(user) if user else None, supplier=request.form)


@web_suppliers_bp.route('/<supplier_id>/delete', methods=['POST'])
@jwt_required()
def delete_supplier(supplier_id):
    supplier = SupplierModel.find_by_id(supplier_id)
    if not supplier:
        flash('Supplier not found.', 'danger')
    else:
        cid = _company_id()
        if str(supplier.get('company_id', '')) != str(cid):
            flash('Access denied.', 'danger')
            return redirect(url_for('web_suppliers.list_suppliers'))
        user_id = get_jwt_identity()
        user_obj = UserModel.find_by_id(user_id)
        SupplierModel.delete(supplier_id)
        EventService.record(cid, 'supplier', supplier_id, supplier.get('name',''), 'deleted',
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Supplier deleted.', 'success')
    return redirect(url_for('web_suppliers.list_suppliers'))