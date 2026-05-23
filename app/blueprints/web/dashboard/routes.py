import logging
from flask import Blueprint, render_template, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.core.models.product_model import ProductModel
from app.core.models.invoice_model import InvoiceModel
from app.core.models.user_model import UserModel
from app.core.models.supplier_model import SupplierModel
from app.core.models.purchase_order_model import PurchaseOrderModel
from app.core.models.goods_receipt_model import GoodsReceiptModel
from app.core.models.supplier_invoice_model import SupplierInvoiceModel
from app.core.models.payment_model import PaymentModel
from app.core.models.customer_quote_model import CustomerQuoteModel
from app.core.models.delivery_note_model import DeliveryNoteModel
from app.core.models.order_model import OrderModel
from app.core.models.customer_model import CustomerModel
from app.core.services.stock_service import StockService
from app.core.services.invoice_service import InvoiceService
from app.core.utils.helpers import oid

logger = logging.getLogger(__name__)
web_dashboard_bp = Blueprint('web_dashboard', __name__, template_folder='../../../templates')


def _company_id():
    claims = get_jwt()
    return claims.get('company_id')


@web_dashboard_bp.route('')
@web_dashboard_bp.route('/')
@jwt_required()
def index():
    try:
        user_id = get_jwt_identity()
        user = UserModel.find_by_id(user_id)
        if not user:
            return render_template('base/error.html', code=401, message='User not found.'), 401

        cid = _company_id()
        cid_oid = oid(cid) if cid else None
        scope = {'company_id': cid_oid} if cid_oid else {}

        product_count = ProductModel.count(scope) if cid else ProductModel.count()
        low_stock = StockService.get_low_stock(cid)
        invoice_counts = InvoiceService.get_counts(cid)
        recent_invoices = InvoiceService.get_recent(5, cid)
        recent_movements = StockService.get_recent_movements(10, cid)
        valuation = StockService.get_total_valuation(cid)
        category_summary = StockService.get_category_summary(cid)
        month_sales = InvoiceService.get_month_sales(cid)
        year_sales = InvoiceService.get_year_sales(cid)

        supplier_count = SupplierModel.count(scope)
        po_count = PurchaseOrderModel.count(scope)
        gr_count = GoodsReceiptModel.count(scope)
        si_count = SupplierInvoiceModel.count(scope)
        payment_count = PaymentModel.count(scope)

        customer_count = CustomerModel.count(scope)
        quote_count = CustomerQuoteModel.count(scope)
        order_count = OrderModel.count(scope)
        dn_count = DeliveryNoteModel.count(scope)

        recent_pos, _ = PurchaseOrderModel.find_all(1, 5, scope)
        recent_sis, _ = SupplierInvoiceModel.find_all(1, 5, scope)
        recent_quotes, _ = CustomerQuoteModel.find_all(1, 5, scope)
        recent_orders = OrderModel.recent(5, scope)
        recent_dns, _ = DeliveryNoteModel.find_all(1, 5, scope)

        return render_template('dashboard/index.html',
                               mode='web',
                               user=UserModel.to_dict(user),
                               product_count=product_count,
                               low_stock=low_stock,
                               low_stock_count=len(low_stock),
                               invoice_counts=invoice_counts,
                               recent_invoices=recent_invoices,
                               recent_movements=recent_movements,
                               valuation=valuation,
                               category_summary=category_summary,
                               month_sales=month_sales,
                               year_sales=year_sales,
                               supplier_count=supplier_count,
                               po_count=po_count,
                               gr_count=gr_count,
                               si_count=si_count,
                               payment_count=payment_count,
                               customer_count=customer_count,
                               quote_count=quote_count,
                               order_count=order_count,
                               dn_count=dn_count,
                               recent_pos=[PurchaseOrderModel.to_dict(p) for p in recent_pos],
                               recent_sis=[SupplierInvoiceModel.to_dict(s) for s in recent_sis],
                               recent_quotes=[CustomerQuoteModel.to_dict(q) for q in recent_quotes],
                               recent_orders=[OrderModel.to_dict(o) for o in recent_orders],
                               recent_dns=[DeliveryNoteModel.to_dict(d) for d in recent_dns])
    except Exception as e:
        logger.exception('Dashboard load error')
        return render_template('base/error.html', code=500, message='Could not load dashboard.'), 500
