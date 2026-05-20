import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.services.stock_service import StockService
from app.core.models.user_model import UserModel
from app.core.utils.helpers import paginate

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
    if request.method == 'GET':
        return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None, product=None)

    try:
        cid = _company_id()
        errors = StockService.validate(request.form.to_dict(), cid)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None, product=request.form)

        user_id = get_jwt_identity()
        StockService.create(request.form.to_dict(), user_id, cid)
        flash('Product created successfully.', 'success')
        return redirect(url_for('web_stock.list_products'))
    except Exception as e:
        logger.exception('Product create error')
        flash('Could not create product.', 'danger')
        return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None, product=request.form)


@web_stock_bp.route('/<product_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_product(product_id):
    user = _get_user()
    cid = _company_id()
    product = StockService.get_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('web_stock.list_products'))

    if request.method == 'GET':
        return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None,
                               product=product)

    try:
        data = request.form.to_dict()
        data['sku'] = product['sku']
        errors = StockService.validate(data, cid, is_update=True)
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None,
                                   product=data)

        user_id = get_jwt_identity()
        StockService.update(product_id, data, user_id, cid)
        flash('Product updated successfully.', 'success')
        return redirect(url_for('web_stock.list_products'))
    except Exception as e:
        logger.exception('Product update error')
        flash('Could not update product.', 'danger')
        return render_template('stock/edit.html', mode='web', user=UserModel.to_dict(user) if user else None,
                               product=request.form)


@web_stock_bp.route('/<product_id>/delete', methods=['POST'])
@jwt_required()
def delete_product(product_id):
    try:
        user_id = get_jwt_identity()
        cid = _company_id()
        if StockService.delete(product_id, user_id, cid):
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
    product = StockService.get_by_id(product_id)
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('web_stock.list_products'))

    try:
        cid = _company_id()
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
    user = _get_user()
    cid = _company_id()
    user_id = get_jwt_identity()

    if request.method == 'GET':
        return render_template('stock/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               results=None)

    if 'file' not in request.files:
        flash('No file selected.', 'danger')
        return render_template('stock/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               results=None)

    file = request.files['file']
    if not file.filename:
        flash('No file selected.', 'danger')
        return render_template('stock/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               results=None)

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''

    rows = []
    if ext == 'json':
        import json
        try:
            raw = json.load(file.stream)
            rows = raw if isinstance(raw, list) else [raw]
        except Exception as e:
            flash(f'Invalid JSON file: {e}', 'danger')
            return render_template('stock/bulk_upload.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None,
                                   results=None)
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
                                       results=None)
        except Exception as e:
            flash(f'Invalid CSV file: {e}', 'danger')
            return render_template('stock/bulk_upload.html', mode='web',
                                   user=UserModel.to_dict(user) if user else None,
                                   results=None)
    else:
        flash('Unsupported format. Please upload a JSON or CSV file.', 'danger')
        return render_template('stock/bulk_upload.html', mode='web',
                               user=UserModel.to_dict(user) if user else None,
                               results=None)

    from bson.objectid import ObjectId
    results = []
    success_count = 0
    for idx, row in enumerate(rows):
        row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        entry = {'row': idx + 1, 'name': row.get('name', ''), 'sku': row.get('sku', ''), 'errors': [], 'status': ''}

        data = {
            'name': row.get('name', ''),
            'sku': row.get('sku', ''),
            'description': row.get('description', ''),
            'quantity': row.get('quantity', '0'),
            'unit_price': row.get('unit_price', '0'),
            'category': row.get('category', ''),
            'tax_rate': row.get('tax_rate', '0'),
            'low_stock_threshold': row.get('low_stock_threshold', '5'),
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
                           results=results)
