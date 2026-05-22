from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from app.models.invoice import InvoiceModel
from app.models.stock import StockModel
from app.services.stock_service import StockService


class InvoiceService:

    @staticmethod
    def validate(data):
        errors = []
        customer_name = (data.get('customer_name') or '').strip()
        if not customer_name:
            errors.append('Customer name is required.')

        items = data.get('items', [])
        if not items or not isinstance(items, list):
            errors.append('At least one item is required.')
            return errors, None

        for idx, item in enumerate(items):
            if not item.get('sku'):
                errors.append(f'Item {idx + 1}: SKU is required.')
            try:
                qty = int(item.get('quantity', 0))
                if qty <= 0:
                    errors.append(f'Item {idx + 1}: Quantity must be positive.')
            except (ValueError, TypeError):
                errors.append(f'Item {idx + 1}: Quantity must be an integer.')

            try:
                price = float(item.get('price', 0))
                if price < 0:
                    errors.append(f'Item {idx + 1}: Unit price cannot be negative.')
            except (ValueError, TypeError):
                errors.append(f'Item {idx + 1}: Unit price must be a number.')

        return errors, {
            'customer_name': customer_name,
            'customer_email': (data.get('customer_email') or '').strip(),
            'notes': (data.get('notes') or '').strip(),
        }

    @staticmethod
    def create(data, user_id):
        items = []
        subtotal = 0.0
        for it in data['items']:
            line_total = int(it['quantity']) * float(it['price'])
            items.append({
                'sku': it['sku'],
                'name': it.get('name', ''),
                'quantity': int(it['quantity']),
                'unit_price': float(it['price']),
                'total': line_total,
            })
            subtotal += line_total

        tax = round(subtotal * 0.10, 2)
        total = round(subtotal + tax, 2)

        invoice_number = f'INV-{InvoiceModel.get_next_sequence():05d}'

        invoice_data = {
            'invoice_number': invoice_number,
            'customer_name': data['customer_name'],
            'customer_email': data.get('customer_email', ''),
            'items': items,
            'subtotal': round(subtotal, 2),
            'tax': tax,
            'total': total,
            'status': 'paid',
            'notes': data.get('notes', ''),
            'created_by': user_id,
        }

        invoice_id = InvoiceModel.create(invoice_data)

        for it in items:
            StockService.deduct_stock(it['sku'], it['quantity'])

        return invoice_id, invoice_number

    @staticmethod
    def get_by_id(invoice_id):
        inv = InvoiceModel.find_by_id(invoice_id)
        return InvoiceModel.to_dict(inv) if inv else None

    @staticmethod
    def list(page, per_page, filters=None):
        items, total = InvoiceModel.find_all(page, per_page, filters)
        return [InvoiceModel.to_dict(item) for item in items], total

    @staticmethod
    def generate_pdf(invoice_id):
        inv = InvoiceModel.find_by_id(invoice_id)
        if not inv:
            return None

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f'<b>INVOICE</b>', styles['Title']))
        elements.append(Paragraph(f'<b>{inv["invoice_number"]}</b>', styles['Normal']))
        elements.append(Spacer(1, 12))

        elements.append(Paragraph(f'<b>Customer:</b> {inv["customer_name"]}', styles['Normal']))
        if inv.get('customer_email'):
            elements.append(Paragraph(f'<b>Email:</b> {inv["customer_email"]}', styles['Normal']))
        elements.append(Spacer(1, 12))

        if inv.get('notes'):
            elements.append(Paragraph(f'<b>Notes:</b> {inv["notes"]}', styles['Normal']))
            elements.append(Spacer(1, 12))

        table_data = [['SKU', 'Item', 'Qty', 'Unit Price', 'Total']]
        for item in inv['items']:
            table_data.append([
                item['sku'],
                item['name'],
                str(item['quantity']),
                f"${item['unit_price']:.2f}",
                f"${item['total']:.2f}",
            ])

        table = Table(table_data, colWidths=[60, 180, 50, 80, 80])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F6')]),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

        summary_data = [
            ['Subtotal:', f"${inv['subtotal']:.2f}"],
            ['Tax (10%):', f"${inv['tax']:.2f}"],
            ['Total:', f"${inv['total']:.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[370, 80])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
            ('LINEBELOW', (0, 2), (-1, 2), 1, colors.black),
        ]))
        elements.append(summary_table)

        doc.build(elements)
        buf.seek(0)
        return buf
