from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.product_model import ProductModel
from app.core.models.user_model import UserModel
from app.core.services.stock_service import StockService
from app.core.utils.helpers import paginate
from bson.objectid import ObjectId

eshop_bp = Blueprint('eshop', __name__, template_folder='../../templates')

def _get_user():
    try:
        uid = get_jwt_identity()
        if uid:
            return UserModel.find_by_id(uid)
    except:
        pass
    return None

def _company_id():
    try:
        claims = get_jwt()
        if claims:
            return claims.get('company_id')
    except:
        pass
    return None

@eshop_bp.route('/')
@eshop_bp.route('')
def index():
    # Try to get company ID, but don't require authentication for browsing
    cid = _company_id()
    
    # Get all active products for the eshop
    filters = {'status': 'active'}
    if cid:
        filters['company_id'] = ObjectId(cid)
    
    products, total = StockService.list(1, 100, filters, cid)
    
    user = _get_user()
    return render_template('eshop/index.html',
                           mode='eshop',
                           user=UserModel.to_dict(user) if user else None,
                           products=products)

@eshop_bp.route('/item/<product_id>')
def product_item(product_id):
    try:
        # Try to get company ID, but don't require authentication for browsing
        cid = _company_id()
        
        product = StockService.get_by_id(product_id, cid)
        if not product:
            flash('Product not found.', 'danger')
            return redirect(url_for('eshop.index'))
        
        user = _get_user()
        return render_template('eshop/product.html',
                               mode='eshop',
                               user=UserModel.to_dict(user) if user else None,
                               product=product)
    except Exception as e:
        flash('Could not load product details.', 'danger')
        return redirect(url_for('eshop.index'))

@eshop_bp.route('/admin')
@jwt_required()
def admin():
    try:
        cid = _company_id()
        if not cid:
            flash('Company not found.', 'danger')
            return redirect(url_for('web_auth.login'))
        
        # Get all products for admin management
        products, total = StockService.list(1, 100, {}, cid)
        
        user = _get_user()
        user_dict = UserModel.to_dict(user) if user else {}
        role_names = user_dict.get('role_names', [])
        # Check if user has permission (Admin or Manager)
        if 'Admin' not in role_names and 'Manager' not in role_names:
            abort(403)
        
        return render_template('eshop/admin.html',
                               mode='eshop',
                               user=UserModel.to_dict(user) if user else None,
                               products=products)
    except Exception as e:
        flash('Could not load Eshop admin.', 'danger')
        return redirect(url_for('web_dashboard.index'))