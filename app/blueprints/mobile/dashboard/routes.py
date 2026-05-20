import logging
from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.product_model import ProductModel
from app.core.models.user_model import UserModel
from app.core.services.stock_service import StockService
from app.core.services.invoice_service import InvoiceService
from app.core.utils.helpers import oid

logger = logging.getLogger(__name__)
mobile_dashboard_bp = Blueprint('mobile_dashboard', __name__, template_folder='../../../templates')


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@mobile_dashboard_bp.route('')
@mobile_dashboard_bp.route('/')
@jwt_required()
def index():
    try:
        user_id = get_jwt_identity()
        user = UserModel.find_by_id(user_id)
        cid = _company_id()
        product_count = ProductModel.count({'company_id': oid(cid)}) if cid else ProductModel.count()
        low_stock = StockService.get_low_stock(cid)
        invoice_counts = InvoiceService.get_counts(cid)
        recent_invoices = InvoiceService.get_recent(5, cid)
        valuation = StockService.get_total_valuation(cid)

        return render_template('dashboard/index.html',
                               mode='mobile',
                               user=UserModel.to_dict(user) if user else None,
                               product_count=product_count,
                               low_stock=low_stock,
                               low_stock_count=len(low_stock),
                               invoice_counts=invoice_counts,
                               recent_invoices=recent_invoices,
                               valuation=valuation,
                               category_summary=[])
    except Exception as e:
        logger.exception('Mobile dashboard error')
        return render_template('base/error.html', code=500, message='Could not load dashboard.'), 500
