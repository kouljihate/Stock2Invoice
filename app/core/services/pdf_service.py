import logging
from io import BytesIO
from fpdf import FPDF

logger = logging.getLogger(__name__)


class InvoicePDF(FPDF):
    def __init__(self, invoice, company):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.invoice = invoice
        self.company = company or {}
        tpl = company.get('invoice_template', {}) if company else {}
        self.pri = tpl.get('primary_color', '#1a73e8')
        self.sec = tpl.get('secondary_color', '#6c757d')
        self.acc = tpl.get('accent_color', '#0d6efd')
        self.show_logo = tpl.get('show_logo', True)
        self.show_legal = tpl.get('show_legal_ids', True)
        self.show_rib = tpl.get('show_rib', True)
        self.header_text = tpl.get('header_text', '')
        self.footer_text = tpl.get('footer_text', '')
        self.payment_terms = tpl.get('payment_terms', '')
        self.sig_name = tpl.get('signature_name', '')
        self.sig_title = tpl.get('signature_title', '')
        self.set_auto_page_break(auto=True, margin=20)

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def render(self):
        self.add_page()
        inv = self.invoice
        company = self.company

        pri_rgb = self.hex_to_rgb(self.pri)
        sec_rgb = self.hex_to_rgb(self.sec)
        acc_rgb = self.hex_to_rgb(self.acc)

        self.set_auto_page_break(auto=True, margin=25)

        # Header section
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(*pri_rgb)
        company_name = company.get('name', '') if company else ''
        if company_name:
            self.cell(0, 8, company_name, new_x='LMARGIN', new_y='NEXT')

        if self.header_text:
            self.set_font('Helvetica', '', 8)
            self.set_text_color(*sec_rgb)
            self.multi_cell(0, 4, self.header_text)
            self.ln(2)

        self.ln(4)

        # Invoice title and number
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(*pri_rgb)
        self.cell(0, 8, 'INVOICE', new_x='LMARGIN', new_y='NEXT')

        self.set_font('Helvetica', '', 10)
        self.set_text_color(*sec_rgb)
        inv_num = inv.get('invoice_number', '')
        self.cell(0, 5, inv_num, new_x='LMARGIN', new_y='NEXT')

        inv_date = inv.get('created_at', '')[:10] if inv.get('created_at') else '-'
        self.set_font('Helvetica', '', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, f'Date: {inv_date}', new_x='LMARGIN', new_y='NEXT')

        if inv.get('delivery_time'):
            self.cell(0, 4, f'Delivery: {inv["delivery_time"]}', new_x='LMARGIN', new_y='NEXT')

        self.ln(6)

        # Bill To
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*sec_rgb)
        self.cell(0, 5, 'Bill To:', new_x='LMARGIN', new_y='NEXT')

        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(40, 40, 40)
        self.cell(0, 5, inv.get('customer_name', ''), new_x='LMARGIN', new_y='NEXT')

        self.set_font('Helvetica', '', 8)
        self.set_text_color(80, 80, 80)
        email = inv.get('contact_email') or inv.get('customer_email', '')
        if email:
            self.cell(0, 4, email, new_x='LMARGIN', new_y='NEXT')
        addr = inv.get('customer_address', '')
        if addr:
            self.multi_cell(0, 4, addr)

        if inv.get('attention_to'):
            self.set_font('Helvetica', '', 8)
            self.set_text_color(*sec_rgb)
            self.cell(0, 4, f'Attn: {inv["attention_to"]}', new_x='LMARGIN', new_y='NEXT')

        self.ln(8)

        # Items table
        col_widths = [25, 55, 15, 25, 25, 25]
        headers = ['SKU', 'Item', 'Qty', 'Price', 'Pack', 'Total']

        # Table header
        self.set_fill_color(*pri_rgb)
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 8)
        for i, h in enumerate(headers):
            align = 'L' if i < 2 else 'R'
            self.cell(col_widths[i], 6, h, border=1, align=align, fill=True)
        self.ln()

        # Table rows
        self.set_text_color(40, 40, 40)
        self.set_font('Helvetica', '', 8)
        for item in inv.get('items', []):
            row = [
                item.get('sku', ''),
                item.get('name', ''),
                str(item.get('quantity', '')),
                f"{item.get('unit_price', 0)} MAD",
                str(item.get('pack_size', '')),
                f"{item.get('total', 0)} MAD",
            ]
            for i, val in enumerate(row):
                align = 'L' if i < 2 else 'R'
                self.cell(col_widths[i], 5, val, border=1, align=align)
            self.ln()

        self.ln(4)

        # Totals
        right_x = self.w - self.r_margin - 60
        total_width = 60
        label_width = self.w - self.r_margin - self.l_margin - total_width

        def total_row(label, value, bold=False, color=None):
            self.set_font('Helvetica', 'B' if bold else '', 9)
            if color:
                self.set_text_color(*color)
            else:
                self.set_text_color(40, 40, 40)
            self.cell(label_width, 6, '', border=0)
            self.cell(total_width, 6, f'{label}', border=0, align='L')
            self.cell(0, 6, value, border=0, align='R', new_x='LMARGIN', new_y='NEXT')

        total_row('Subtotal', f"{inv.get('subtotal', 0)} MAD")
        if inv.get('discount_percent', 0) > 0:
            total_row(f"Discount ({inv['discount_percent']}%)", f"-{inv.get('discount_amount', 0)} MAD", color=(220, 50, 50))
        total_row(f"Tax ({inv.get('tax_percent', 0)}%)", f"{inv.get('tax_amount', 0)} MAD")
        self.ln(1)
        total_row('Total', f"{inv.get('total', 0)} MAD", bold=True, color=acc_rgb)

        self.ln(6)

        # Payment terms
        if self.payment_terms:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(*sec_rgb)
            self.cell(0, 4, 'Payment Terms: ' + self.payment_terms, new_x='LMARGIN', new_y='NEXT')
            self.ln(4)

        # Notes
        notes = inv.get('notes', '')
        if notes:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(80, 80, 80)
            self.cell(0, 4, 'Notes:', new_x='LMARGIN', new_y='NEXT')
            self.multi_cell(0, 4, notes)
            self.ln(4)

        return self

    def footer(self):
        self.set_y(-22)
        self.set_font('Helvetica', '', 7)
        self.set_text_color(120, 120, 120)

        company = self.company
        if not company:
            self.cell(0, 4, '', new_x='LMARGIN', new_y='NEXT')
            return

        # Left footer
        left_lines = []
        name = company.get('name', '')
        if name:
            left_lines.append(name)
        addr_parts = []
        if company.get('address'):
            addr_parts.append(company['address'])
        if company.get('city'):
            addr_parts.append(company['city'])
        if addr_parts:
            left_lines.append(', '.join(addr_parts))
        if company.get('phone'):
            left_lines.append(f"Tel: {company['phone']}")
        if company.get('email'):
            left_lines.append(f"Email: {company['email']}")

        x_left = self.l_margin
        self.set_xy(x_left, self.get_y())
        for line in left_lines:
            self.set_x(x_left)
            self.cell(self.w / 2 - self.l_margin, 3.5, line, new_x='LMARGIN', new_y='NEXT')

        # Right footer
        right_lines = []
        if company.get('rib') and self.show_rib:
            right_lines.append(f"RIB: {company['rib']}")
        if self.show_legal:
            if company.get('if_tax'):
                right_lines.append(f"IF: {company['if_tax']}")
            if company.get('tp'):
                right_lines.append(f"TP: {company['tp']}")
            if company.get('rc'):
                right_lines.append(f"RC: {company['rc']}")
            if company.get('ice'):
                right_lines.append(f"ICE: {company['ice']}")

        right_x = self.w / 2 + self.l_margin
        self.set_xy(right_x, self.get_y() - len(left_lines) * 3.5)
        for line in right_lines:
            self.set_x(right_x)
            self.cell(self.w / 2 - self.r_margin, 3.5, line, align='R', new_x='LMARGIN', new_y='NEXT')

        # Extra footer text / signature
        extra_y = self.get_y() + 2
        if self.footer_text or (self.sig_name and self.sig_title):
            if self.footer_text:
                self.set_xy(x_left, extra_y)
                self.set_font('Helvetica', 'I', 6)
                self.multi_cell(self.w / 2 - self.l_margin, 3, self.footer_text)
            if self.sig_name and self.sig_title:
                self.set_xy(right_x, extra_y)
                self.set_font('Helvetica', '', 7)
                self.cell(self.w / 2 - self.r_margin, 3, 'Authorized by', align='R', new_x='LMARGIN', new_y='NEXT')
                self.set_x(right_x)
                self.set_font('Helvetica', 'B', 7)
                self.cell(self.w / 2 - self.r_margin, 3, self.sig_name, align='R', new_x='LMARGIN', new_y='NEXT')
                self.set_x(right_x)
                self.set_font('Helvetica', '', 6)
                self.cell(self.w / 2 - self.r_margin, 3, self.sig_title, align='R', new_x='LMARGIN', new_y='NEXT')


def generate_invoice_pdf(invoice, company):
    pdf = InvoicePDF(invoice, company)
    pdf.render()
    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf
