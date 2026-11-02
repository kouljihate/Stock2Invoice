"""Public document shapes — exact ports of the monolith's model ``to_dict``."""

from si_common.ids import as_str, iso


def supplier_out(s):
    if not s:
        return None
    return {
        'id': str(s['_id']),
        'name': s.get('name'),
        'contact_name': s.get('contact_name', ''),
        'email': s.get('email', ''),
        'phone': s.get('phone', ''),
        'address': s.get('address', ''),
        'city': s.get('city', ''),
        'ice': s.get('ice', ''),
        'rc': s.get('rc', ''),
        'payment_terms': s.get('payment_terms', ''),
        'company_id': as_str(s.get('company_id')),
        'created_at': iso(s.get('created_at')),
    }


def po_out(po):
    if not po:
        return None
    return {
        'id': str(po['_id']),
        'po_number': po.get('po_number'),
        'supplier_id': as_str(po.get('supplier_id')),
        'supplier_name': po.get('supplier_name', ''),
        'items': po.get('items', []),
        'subtotal': float(po.get('subtotal', 0)),
        'discount_percent': float(po.get('discount_percent', 0)),
        'discount_amount': float(po.get('discount_amount', 0)),
        'tax_percent': float(po.get('tax_percent', 0)),
        'tax_amount': float(po.get('tax_amount', 0)),
        'total': float(po.get('total', 0)),
        'status': po.get('status', 'draft'),
        'notes': po.get('notes', ''),
        'company_id': as_str(po.get('company_id')),
        'created_by': as_str(po.get('created_by')),
        'created_at': iso(po.get('created_at')),
    }


def gr_out(gr):
    if not gr:
        return None
    return {
        'id': str(gr['_id']),
        'receipt_number': gr.get('receipt_number'),
        'po_id': as_str(gr.get('po_id')),
        'po_number': gr.get('po_number', ''),
        'supplier_id': as_str(gr.get('supplier_id')),
        'supplier_name': gr.get('supplier_name', ''),
        'items': gr.get('items', []),
        'notes': gr.get('notes', ''),
        'status': gr.get('status', 'waiting'),
        'company_id': as_str(gr.get('company_id')),
        'created_by': as_str(gr.get('created_by')),
        'created_at': iso(gr.get('created_at')),
    }


def si_out(inv):
    if not inv:
        return None
    return {
        'id': str(inv['_id']),
        'invoice_number': inv.get('invoice_number'),
        'supplier_id': as_str(inv.get('supplier_id')),
        'supplier_name': inv.get('supplier_name', ''),
        'po_id': as_str(inv.get('po_id')),
        'po_number': inv.get('po_number', ''),
        'invoice_date': iso(inv.get('invoice_date')),
        'due_date': iso(inv.get('due_date')),
        'items': inv.get('items', []),
        'subtotal': float(inv.get('subtotal', 0)),
        'discount_percent': float(inv.get('discount_percent', 0)),
        'discount_amount': float(inv.get('discount_amount', 0)),
        'tax_percent': float(inv.get('tax_percent', 0)),
        'tax_amount': float(inv.get('tax_amount', 0)),
        'total': float(inv.get('total', 0)),
        'status': inv.get('status', 'draft'),
        'notes': inv.get('notes', ''),
        'company_id': as_str(inv.get('company_id')),
        'created_by': as_str(inv.get('created_by')),
        'created_at': iso(inv.get('created_at')),
    }


def payment_out(p):
    if not p:
        return None
    return {
        'id': str(p['_id']),
        'payment_number': p.get('payment_number'),
        'supplier_id': as_str(p.get('supplier_id')),
        'supplier_name': p.get('supplier_name', ''),
        'invoice_id': as_str(p.get('invoice_id')),
        'invoice_number': p.get('invoice_number', ''),
        'amount': float(p.get('amount', 0)),
        'payment_date': iso(p.get('payment_date')),
        'payment_method': p.get('payment_method', ''),
        'reference': p.get('reference', ''),
        'notes': p.get('notes', ''),
        'status': p.get('status', 'pending'),
        'company_id': as_str(p.get('company_id')),
        'created_by': as_str(p.get('created_by')),
        'created_at': iso(p.get('created_at')),
    }
