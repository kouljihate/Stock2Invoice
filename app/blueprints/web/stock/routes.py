import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.services.stock_service import StockService
from app.core.models.user_model import UserModel
from app.core.models.product_model import ProductModel
from app.core.models.supplier_model import SupplierModel
from app.core.services.event_service import EventService
from app.core.utils.helpers import paginate
from bson.objectid import ObjectId

logger = logging.getLogger(__name__)
web_stock_bp = Blueprint('web_stock', __name__, template_folder='../../../templates')


def _get_user():
    uid = get_jwt_identity()
    return UserModel.find_by_id(uid)


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_stock_bp.route('')
@web_stock_bp.route('/')
@jwt_required()
def list_products():
    try:
        page, per_page = paginate(request.args.get('page', 1), request.args.get('per_page', 20))
        filters = {}
        if request.args.get('category'):
            filters['category'] = request.args['category']
        if request.args.get('search'):
            import re
            regex = {'$regex': re.escape(request.args['search']), '$options': 'i'}
            filters['$or'] = [{'name': regex}, {'sku': regex}]
        if request.args.get('status'):
            filters['status'] = request.args['status']
        if request.args.get('low_stock'):
            filters['$expr'] = {'$lte': ['$quantity', '$quantity_min']}
        cid = _company_id()
        items, total = StockService.list(page, per_page, filters, cid)
        user = _get_user()
        return render_template('stock/list.html',
                               mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               products=items,
                               total=total,
                               page=page,
                               per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception as e:
        logger.exception('Product list error')
        flash('Could not load products.', 'danger')
        return render_template('stock/list.html', mode='web', products=[], total=0, page=1, per_page=20, pages=0)


@web_stock_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_product():
    user = _get_user()
    cid = _company_id()
    suppliers = []
    if cid:
        suppliers = [SupplierModel.to_dict(s) for s in SupplierModel.find_all_unpaginated({'company_id': ObjectId(cid)})]
    if request.method == 'GET':
        return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None, product=None, suppliers=suppliers)

    try:
        cid = _company_id()
        data = request.form.to_dict()
        if data.get('supplier_id'):
            sup = SupplierModel.find_by_id(data['supplier_id'])
            data['supplier_name'] = sup.get('name', '') if sup else ''
        errors = StockService.validate(data, cid)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None, product=data, suppliers=suppliers)

        user_id = get_jwt_identity()
        StockService.create(data, user_id, cid)
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'product', '', request.form.get('sku',''), 'created',
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Product created successfully.', 'success')
        return redirect(url_for('web_stock.list_products'))
    except Exception as e:
        logger.exception('Product create error')
        flash('Could not create product.', 'danger')
        return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None, product=request.form, suppliers=suppliers)


@web_stock_bp.route('/<product_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_product(product_id):
    user = _get_user()
    cid = _company_id()
    product = StockService.get_by_id(product_id, cid)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('web_stock.list_products'))

    if request.method == 'GET':
        suppliers = []
        if cid:
            suppliers = [SupplierModel.to_dict(s) for s in SupplierModel.find_all_unpaginated({'company_id': ObjectId(cid)})]
        return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None,
                               product=product, suppliers=suppliers)

    try:
        data = request.form.to_dict()
        data['sku'] = product['sku']
        if data.get('supplier_id'):
            sup = SupplierModel.find_by_id(data['supplier_id'])
            data['supplier_name'] = sup.get('name', '') if sup else ''
        errors = StockService.validate(data, cid, is_update=True)
        if errors:
            for e in errors:
                flash(e, 'danger')
            suppliers = []
            if cid:
                suppliers = [SupplierModel.to_dict(s) for s in SupplierModel.find_all_unpaginated({'company_id': ObjectId(cid)})]
            return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None,
                                   product=data, suppliers=suppliers)

        user_id = get_jwt_identity()
        StockService.update(product_id, data, user_id, cid)
        user_obj = UserModel.find_by_id(user_id)
        EventService.record(cid, 'product', product_id, product.get('sku',''), 'updated',
                            changes={'field': 'details', 'old_value': '', 'new_value': 'updated'},
                            user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
        flash('Product updated successfully.', 'success')
        return redirect(url_for('web_stock.list_products'))
    except Exception as e:
        logger.exception('Product update error')
        flash('Could not update product.', 'danger')
        suppliers = []
        if cid:
            suppliers = [SupplierModel.to_dict(s) for s in SupplierModel.find_all_unpaginated({'company_id': ObjectId(cid)})]
        return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None,
                               product=request.form, suppliers=suppliers)


@web_stock_bp.route('/<product_id>/delete', methods=['POST'])
@jwt_required()
def delete_product(product_id):
    try:
        user_id = get_jwt_identity()
        cid = _company_id()
        product = StockService.get_by_id(product_id, cid)
        if StockService.delete(product_id, user_id, cid):
            user_obj = UserModel.find_by_id(user_id)
            EventService.record(cid, 'product', product_id, product.get('sku','') if product else '', 'deleted',
                                user_id=user_id, user_name=user_obj.get('name','') if user_obj else '')
            flash('Product deleted.', 'success')
        else:
            flash('Product not found.', 'danger')
    except Exception as e:
        logger.exception('Product delete error')
        flash('Could not delete product.', 'danger')
    return redirect(url_for('web_stock.list_products'))


@web_stock_bp.route('/<product_id>')
@jwt_required()
def view_product(product_id):
    user = _get_user()
    cid = _company_id()
    product = StockService.get_by_id(product_id, cid)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('web_stock.list_products'))

    try:
        page, per_page = paginate(request.args.get('page', 1), 20)
        movements, total = StockService.get_movements(page, per_page, product_id, cid)
        return render_template('stock/detail.html', mode='web', user=UserModel.to_dict(user) if user else None,
                               product=product, movements=movements, total=total, page=page, per_page=per_page,
                               pages=(total + per_page - 1) // per_page)
    except Exception as e:
        logger.exception('Product detail error')
        return render_template('stock/detail.html', mode='web', user=UserModel.to_dict(user) if user else None,
                               product=product, movements=[], total=0, page=1, per_page=20, pages=0)


@web_stock_bp.route('/bulk-upload', methods=['GET', 'POST'])
@jwt_required()
def bulk_upload():
    import json
    user = _get_user()
    cid = _company_id()
    user_id = get_jwt_identity()

    if request.method == 'GET':
        return render_template('stock/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=None)

    json_data = request.form.get('json_data')
    if json_data:
        rows = json.loads(json_data)
        results = []
        success_count = 0
        for idx, row in enumerate(rows):
            entry = {'row': idx + 1, 'name': row.get('name', ''), 'sku': row.get('sku', ''), 'errors': [], 'status': ''}
            def _status(v):
                if not v: return 'active'
                return 'active' if v.strip().lower() in ('actif', 'active', '') else v.strip().lower()
            data = {
                'name': row.get('name', ''),
                'sku': row.get('sku', ''),
                'description': row.get('description', ''),
                'quantity': row.get('stock_quantity', row.get('quantity', '0')),
                'price': row.get('sale_price', row.get('price', '0')),
                'purchase_price': row.get('purchase_price', '0'),
                'category': row.get('category', ''),
                'subcategory': row.get('subcategory', ''),
                'package_type': row.get('package_type', ''),
                'brand': row.get('brand', ''),
                'supplier_id': row.get('supplier_id', ''),
                'supplier_name': row.get('supplier_name', ''),
                'pack_size': row.get('pack_size', '0'),
                'pack_size_unit': row.get('pack_size_unit', ''),
                'number_of_pack': row.get('number_of_pack', '0'),
                'quantity_min': row.get('stock_min_quantity', row.get('quantity_min', '5')),
                'status': _status(row.get('status', '')),
            }
            errs = StockService.validate(data, cid)
            if errs:
                entry['errors'] = errs
                entry['status'] = 'error'
                results.append(entry)
                continue
            try:
                StockService.create(data, user_id, cid)
                entry['status'] = 'success'
                success_count += 1
            except Exception as e:
                entry['errors'] = [str(e)]
                entry['status'] = 'error'
            results.append(entry)
        flash(f'{success_count} of {len(rows)} products imported successfully.', 'success')
        return render_template('stock/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=results)

    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return render_template('stock/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=None)

    file = request.files['file']
    if not file.filename:
        flash('No file selected.', 'danger')
        return render_template('stock/bulk_upload.html', mode='web',
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
            return render_template('stock/bulk_upload.html', mode='web',
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
                return render_template('stock/bulk_upload.html', mode='web',
                                       user=UserModel.to_dict(user) if user else None,
                                       preview=None, results=None)
        except Exception as e:
            flash(f'Invalid CSV file: {e}', 'danger')
            return render_template('stock/bulk_upload.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None,
                                   preview=None, results=None)
    else:
        flash('Unsupported format. Please upload a JSON or CSV file.', 'danger')
        return render_template('stock/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               preview=None, results=None)

    cleaned = []
    for row in rows:
        r = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        cleaned.append({
            'name': r.get('name', ''),
            'sku': r.get('sku', ''),
            'description': r.get('description', ''),
            'quantity': r.get('stock_quantity', r.get('quantity', '0')),
            'price': r.get('sale_price', r.get('price', '0')),
            'purchase_price': r.get('purchase_price', '0'),
            'category': r.get('category', ''),
            'subcategory': r.get('subcategory', ''),
            'package_type': r.get('package_type', ''),
            'brand': r.get('brand', ''),
            'supplier_id': r.get('supplier_id', ''),
            'supplier_name': r.get('supplier_name', ''),
            'pack_size': r.get('pack_size', '0'),
            'pack_size_unit': r.get('pack_size_unit', ''),
            'number_of_pack': r.get('number_of_pack', '0'),
            'quantity_min': r.get('stock_min_quantity', r.get('quantity_min', '5')),
            'status': r.get('status', 'active'),
        })

    return render_template('stock/bulk_upload.html', mode='web',
                           user=UserModel.to_dict(user) if user else None,
                           preview=cleaned, results=None)


@web_stock_bp.route('/api/lookup')
@jwt_required()
def api_lookup():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    cid = _company_id()
    products = ProductModel.search_by_sku_or_name(q, cid, limit=10)
    return jsonify([{
        'sku': p.get('sku', ''),
        'name': p.get('name', ''),
        'price': float(p.get('price', 0)),
        'quantity': p.get('quantity', 0),
        'package_type': p.get('package_type', ''),
        'pack_size': p.get('pack_size', ''),
        'pack_size_unit': p.get('pack_size_unit', ''),
    } for p in products])
