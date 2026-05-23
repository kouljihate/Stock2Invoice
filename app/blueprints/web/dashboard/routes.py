import logging
from datetime import datetime, timezone, timedelta
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
from app.extensions.db import mongo

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
        now = datetime.now(timezone.utc)

        low_stock = StockService.get_low_stock(cid)
        month_sales = InvoiceService.get_month_sales(cid)
        year_sales = InvoiceService.get_year_sales(cid)
        valuation = StockService.get_total_valuation(cid)
        category_summary = StockService.get_category_summary(cid)
        recent_movements = StockService.get_recent_movements(10, cid)

        supplier_count = SupplierModel.count(scope)
        po_count = PurchaseOrderModel.count(scope)
        gr_count = GoodsReceiptModel.count(scope)
        si_count = SupplierInvoiceModel.count(scope)
        payment_count = PaymentModel.count(scope)
        customer_count = CustomerModel.count(scope)
        quote_count = CustomerQuoteModel.count(scope)
        order_count = OrderModel.count(scope)
        dn_count = DeliveryNoteModel.count(scope)

        invoice_counts = InvoiceService.get_counts(cid)
        recent_invoices = InvoiceService.get_recent(5, cid)

        po_statuses = list(mongo.db['purchase_orders'].aggregate([
            {'$match': scope},
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}},
        ]))
        po_status_map = {p['_id']: p['count'] for p in po_statuses}

        pending_po_count = po_count - po_status_map.get('received', 0)
        received_gr_count = gr_count

        cashflow_data = list(mongo.db['invoices'].aggregate([
            {'$match': {**scope, 'created_at': {'$gte': now - timedelta(days=180)}}},
            {'$group': {
                '_id': {'$dateToString': {'format': '%Y-%m', 'date': '$created_at'}},
                'inflow': {'$sum': {'$cond': [{'$eq': ['$status', 'paid']}, '$total', 0]}},
                'count': {'$sum': 1},
            }},
            {'$sort': {'_id': 1}},
        ]))
        outflow_data = list(mongo.db['supplier_invoices'].aggregate([
            {'$match': {**scope, 'due_date': {'$gte': now - timedelta(days=180)}}},
            {'$group': {
                '_id': {'$dateToString': {'format': '%Y-%m', 'date': '$due_date'}},
                'outflow': {'$sum': {'$cond': [{'$ne': ['$status', 'paid']}, '$total', 0]}},
                'count': {'$sum': 1},
            }},
            {'$sort': {'_id': 1}},
        ]))
        cf_labels = sorted(set(
            [c['_id'] for c in cashflow_data] +
            [o['_id'] for o in outflow_data]
        ))
        cf_inflow = []
        cf_outflow = []
        cf_map_in = {c['_id']: float(c['inflow']) for c in cashflow_data}
        cf_map_out = {o['_id']: float(o['outflow']) for o in outflow_data}
        for lbl in cf_labels:
            cf_inflow.append(cf_map_in.get(lbl, 0))
            cf_outflow.append(cf_map_out.get(lbl, 0))

        overdue_invoices = list(mongo.db['invoices'].find({
            **scope, 'due_date': {'$lt': now}, 'status': {'$nin': ['paid', 'cancelled']}
        }).sort('due_date', 1))
        overdue_total = sum(float(inv.get('total', 0)) for inv in overdue_invoices)
        overdue_count = len(overdue_invoices)

        overdue_supplier = list(mongo.db['supplier_invoices'].find({
            **scope, 'due_date': {'$lt': now}, 'status': {'$nin': ['paid', 'cancelled']}
        }).sort('due_date', 1))

        suppliers = SupplierModel.find_all_unpaginated(scope)

        pending_grs = list(mongo.db['purchase_orders'].find({
            **scope, 'status': {'$nin': ['received', 'cancelled']}
        }).sort('created_at', -1).limit(10))

        active_quotes = list(mongo.db['customer_quotes'].find({
            **scope, 'status': {'$in': ['draft', 'sent']}
        }).sort('valid_until', 1).limit(10))

        orders_ready = list(mongo.db['orders'].find({
            **scope, 'status': 'confirmed'
        }).sort('created_at', -1).limit(10))

        recent_pos, _ = PurchaseOrderModel.find_all(1, 5, scope)
        recent_sis, _ = SupplierInvoiceModel.find_all(1, 5, scope)
        recent_quotes, _ = CustomerQuoteModel.find_all(1, 5, scope)
        recent_orders = OrderModel.recent(5, scope)
        recent_dns, _ = DeliveryNoteModel.find_all(1, 5, scope)
        recent_payments, _ = PaymentModel.find_all(1, 5, scope)

        return render_template('dashboard/index.html',
                               mode='web',
                               user=UserModel.to_dict(user),
                               now=now,
                               low_stock=low_stock,
                               low_stock_count=len(low_stock),
                               month_sales=month_sales,
                               year_sales=year_sales,
                               valuation=valuation,
                               category_summary=category_summary,
                               recent_movements=recent_movements,
                               supplier_count=supplier_count,
                               po_count=po_count,
                               gr_count=gr_count,
                               si_count=si_count,
                               payment_count=payment_count,
                               customer_count=customer_count,
                               quote_count=quote_count,
                               order_count=order_count,
                               dn_count=dn_count,
                               invoice_counts=invoice_counts,
                               recent_invoices=recent_invoices,
                               po_status_map=po_status_map,
                               pending_po_count=pending_po_count,
                               received_gr_count=received_gr_count,
                               cf_labels=cf_labels,
                               cf_inflow=cf_inflow,
                               cf_outflow=cf_outflow,
                               overdue_total=overdue_total,
                               overdue_count=overdue_count,
                               overdue_invoices=overdue_invoices[:5],
                               overdue_supplier=overdue_supplier[:5],
                               suppliers=suppliers,
                               pending_grs=[PurchaseOrderModel.to_dict(p) for p in pending_grs],
                               active_quotes=[CustomerQuoteModel.to_dict(q) for q in active_quotes],
                               orders_ready=[OrderModel.to_dict(o) for o in orders_ready],
                               recent_pos=[PurchaseOrderModel.to_dict(p) for p in recent_pos],
                               recent_sis=[SupplierInvoiceModel.to_dict(s) for s in recent_sis],
                               recent_quotes=[CustomerQuoteModel.to_dict(q) for q in recent_quotes],
                               recent_orders=[OrderModel.to_dict(o) for o in recent_orders],
                               recent_dns=[DeliveryNoteModel.to_dict(d) for d in recent_dns],
                               recent_payments=[PaymentModel.to_dict(p) for p in recent_payments])
    except Exception as e:
        logger.exception('Dashboard load error')
        return render_template('base/error.html', code=500, message='Could not load dashboard.'), 500
