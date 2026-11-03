import logging
import os
from io import BytesIO
from fpdf import FPDF
from app.number_to_french import number_to_french

logger = logging.getLogger(__name__)

# Absolute path to app/static, resolved from this module so PDF generation
# works no matter what the process working directory is. Two layouts exist:
# a repo checkout (services/workers/app -> <root>/app/static) and the
# workers image (service code at /srv/service/app, assets at /srv/app/static).
def _static_dir():
    here = os.path.abspath(os.path.dirname(__file__))
    for cand in (os.path.join(here, '..', '..', '..', 'app', 'static'),
                 '/srv/app/static'):
        cand = os.path.abspath(cand)
        if os.path.isdir(cand):
            return cand
    return os.path.abspath(os.path.join(here, '..', '..', '..', 'app', 'static'))


STATIC_DIR = _static_dir()


def static_path(*parts):
    """Absolute path under app/static. Leaf names are stripped of directories."""
    safe = [os.path.basename(p) for p in parts]
    return os.path.join(STATIC_DIR, *safe)

A4_W = 210
A4_H = 297
MARGIN = 10
USABLE_W = A4_W - 2 * MARGIN
USABLE_H = A4_H - 2 * MARGIN
HEADER_PCT = 0.20
BODY_PCT = 0.70
FOOTER_PCT = 0.10
HEADER_H = USABLE_H * HEADER_PCT
BODY_H = USABLE_H * BODY_PCT
HEADER_END = MARGIN + HEADER_H


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
        self.footer_text = tpl.get('footer_text', '')
        self.payment_terms = tpl.get('payment_terms', '')
        self.sig_name = tpl.get('signature_name', '')
        self.sig_title = tpl.get('signature_title', '')
        self.set_auto_page_break(auto=True, margin=MARGIN + FOOTER_PCT * USABLE_H)
        font = static_path('fonts', 'Comfortaa-Variable.ttf')
        self.add_font('Comfortaa', '', font)
        self.add_font('Comfortaa', 'B', font)
        self.add_font('Comfortaa', 'I', font)

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def render_header_zone(self, inv, company, pri_rgb, sec_rgb):
        # Logo - left side
        y0 = MARGIN
        self.set_xy(MARGIN, y0)
        logo_path = company.get('logo', '') if company else ''
        logo_y = y0 + 2
        if logo_path and self.show_logo:
            full_path = static_path('uploads', 'logos', logo_path)
            try:
                self.image(full_path, x=MARGIN, y=logo_y, w=70)
                logo_y += 25
            except Exception:
                logger.warning('Invoice logo could not be embedded: %s', logo_path)

        # Subtitle below logo
        self.set_xy(MARGIN, logo_y)
        self.set_font('Comfortaa', '', 6)
        self.set_text_color(100, 100, 100)
        self.cell(55, 4, "Equipement d'eau potable, Eau du bien-\u00eatre, Spa et piscines.", new_x='LMARGIN', new_y='NEXT')

        # Bill To - right side
        right_x = A4_W / 2
        self.set_xy(right_x, y0 + 4)
        self.set_font('Comfortaa', 'B', 9)
        self.set_text_color(*sec_rgb)
        self.cell(0, 5, 'Bill To:', new_x='LMARGIN', new_y='NEXT', align='R')

        self.set_font('Comfortaa', 'B', 12)
        self.set_text_color(40, 40, 40)
        cname = inv.get('customer_name', '')
        self.cell(0, 5, cname, new_x='LMARGIN', new_y='NEXT', align='R')

        self.set_font('Comfortaa', '', 8)
        self.set_text_color(80, 80, 80)
        email = inv.get('contact_email') or inv.get('customer_email', '')
        if email:
            self.cell(0, 4, email, new_x='LMARGIN', new_y='NEXT', align='R')
        addr = inv.get('customer_address', '')
        if addr:
            rh = self.get_string_width(addr) / (A4_W / 2 - MARGIN)
            if rh > 1:
                self.multi_cell(A4_W / 2 - MARGIN, 4, addr, align='R')
            else:
                self.cell(0, 4, addr, new_x='LMARGIN', new_y='NEXT', align='R')
        city = inv.get('customer_city', '')
        if city:
            self.cell(0, 4, city, new_x='LMARGIN', new_y='NEXT', align='R')

    def render_body(self, inv, company, pri_rgb, sec_rgb, acc_rgb):
        self.set_y(HEADER_END + 8)

        # INVOICE title + ref on left, Attention To on right
        inv_num = inv.get('invoice_number', '')
        self.set_font('Comfortaa', 'B', 16)
        self.set_text_color(*pri_rgb)
        title_w = self.get_string_width('INVOICE: ' + inv_num)
        self.cell(title_w + 3, 8, 'INVOICE: ' + inv_num)

        attn = inv.get('attention_to') or inv.get('contact_name', '')
        if attn:
            attn_label = f'Attention To: {attn}'
            attn_w = self.get_string_width(attn_label)
            remaining = USABLE_W - (title_w + 3)
            if attn_w < remaining:
                self.set_font('Comfortaa', '', 12)
                self.set_text_color(*sec_rgb)
                self.cell(0, 8, attn_label, align='R', new_x='LMARGIN', new_y='NEXT')
            else:
                self.set_x(self.l_margin)
                self.ln()
                self.set_font('Comfortaa', '', 12)
                self.set_text_color(*sec_rgb)
                self.cell(0, 5, attn_label, new_x='LMARGIN', new_y='NEXT')
        else:
            self.set_x(self.l_margin)
            self.ln()

        inv_date = inv.get('created_at', '')[:10] if inv.get('created_at') else '-'
        self.set_font('Comfortaa', '', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, f'Date: {inv_date}', new_x='LMARGIN', new_y='NEXT')

        if inv.get('delivery_time'):
            self.cell(0, 4, f'Delivery: {inv["delivery_time"]}', new_x='LMARGIN', new_y='NEXT')

        self.ln(5)

        # Items table - full width
        n_cols = 6
        col_widths = [25, 55, 15, 30, 25, 30]
        # Adjust to fit full width
        total_col = sum(col_widths)
        ratio = USABLE_W / total_col
        col_widths = [int(w * ratio) for w in col_widths]
        headers = ['SKU', 'Item', 'Qty', 'Unit Price', 'Pack Size', 'Total']

        self.set_fill_color(*pri_rgb)
        self.set_text_color(255, 255, 255)
        self.set_font('Comfortaa', 'B', 8)
        x_start = MARGIN
        self.set_x(x_start)
        for i, h in enumerate(headers):
            align = 'L' if i < 2 else 'R'
            self.cell(col_widths[i], 7, h, border=1, align=align, fill=True)
        self.ln()

        self.set_text_color(40, 40, 40)
        self.set_font('Comfortaa', '', 8)
        for item in inv.get('items', []):
            row = [
                item.get('sku', ''),
                item.get('name', ''),
                str(item.get('quantity', '')),
                f"{item.get('unit_price', 0)} MAD",
                str(item.get('pack_size', '')),
                f"{item.get('total', 0)} MAD",
            ]
            self.set_x(x_start)
            for i, val in enumerate(row):
                align = 'L' if i < 2 else 'R'
                self.cell(col_widths[i], 6, val, border=1, align=align)
            self.ln()

        self.ln(4)

        # Totals
        self.set_x(x_start)
        total_col_w = sum(col_widths)
        total_w = 55
        label_w = total_col_w - total_w
        self.set_x(x_start + label_w)
        self.set_font('Comfortaa', '', 9)
        sub = inv.get('subtotal', 0)
        self.cell(total_w, 6, f'Subtotal', border=0, align='L')
        self.cell(0, 6, f'{sub} MAD', border=0, align='R', new_x='LMARGIN', new_y='NEXT')

        if inv.get('discount_percent', 0) > 0:
            self.set_x(x_start + label_w)
            self.set_text_color(220, 50, 50)
            self.cell(total_w, 6, f'Discount ({inv["discount_percent"]}%)', border=0, align='L')
            self.cell(0, 6, f'-{inv.get("discount_amount", 0)} MAD', border=0, align='R', new_x='LMARGIN', new_y='NEXT')

        self.set_x(x_start + label_w)
        self.set_text_color(40, 40, 40)
        self.cell(total_w, 6, f'Tax ({inv.get("tax_percent", 0)}%)', border=0, align='L')
        self.cell(0, 6, f'{inv.get("tax_amount", 0)} MAD', border=0, align='R', new_x='LMARGIN', new_y='NEXT')

        self.set_x(x_start + label_w)
        self.set_font('Comfortaa', 'B', 11)
        self.set_text_color(*acc_rgb)
        self.cell(total_w, 7, 'Total', border=0, align='L')
        self.cell(0, 7, f'{inv.get("total", 0)} MAD', border=0, align='R', new_x='LMARGIN', new_y='NEXT')

        # Arr\u00eat\u00e9 - computed dynamically, just after total
        self.set_x(x_start)
        self.ln(4)
        total_val = inv.get('total', 0)
        arrete = f"Arr\u00eat\u00e9e la pr\u00e9sente facture \u00e0 la somme de {total_val} MAD (en lettres : {number_to_french(total_val)})"
        self.set_font('Comfortaa', 'I', 7)
        self.set_text_color(80, 80, 80)
        self.multi_cell(USABLE_W, 4, arrete, align='L')

        self.ln(2)

        # Payment terms
        if self.payment_terms:
            self.set_x(x_start)
            self.set_font('Comfortaa', 'I', 6)
            self.set_text_color(*sec_rgb)
            self.cell(0, 4, f'Payment Terms: {self.payment_terms}', new_x='LMARGIN', new_y='NEXT')

        # Notes - at bottom of body, centered
        notes_text = "Nous sommes \u00e0 votre disposition pour tout compl\u00e9ment d'informations. Nous vous prions d'agr\u00e9er, Cher Client nos meilleures salutations."
        body_bottom = HEADER_END + BODY_H - 15
        if self.get_y() < body_bottom:
            self.set_y(body_bottom)
        self.set_x(x_start)
        self.set_font('Comfortaa', 'I', 7)
        self.set_text_color(80, 80, 80)
        self.multi_cell(USABLE_W, 5, notes_text, align='C')

        return self

    def footer(self):
        self.set_y(-(MARGIN + FOOTER_PCT * USABLE_H))
        self.set_font('Comfortaa', '', 7)
        self.set_text_color(120, 120, 120)

        company = self.company
        if not company:
            self.cell(0, 4, '', new_x='LMARGIN', new_y='NEXT')
            return

        y0 = self.get_y()

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

        x_left = MARGIN
        self.set_xy(x_left, y0)
        for line in left_lines:
            self.set_x(x_left)
            self.cell(A4_W / 2 - MARGIN, 3.5, line, new_x='LMARGIN', new_y='NEXT')

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

        right_x = A4_W / 2 + MARGIN
        self.set_xy(right_x, y0)
        for line in right_lines:
            self.set_x(right_x)
            self.cell(A4_W / 2 - MARGIN, 3.5, line, align='R', new_x='LMARGIN', new_y='NEXT')

        # Extra footer text / signature
        extra_y = max(self.get_y(), y0 + len(left_lines) * 3.5) + 1
        if self.footer_text or (self.sig_name and self.sig_title):
            if self.footer_text:
                self.set_xy(x_left, extra_y)
                self.set_font('Comfortaa', 'I', 6)
                self.multi_cell(A4_W / 2 - MARGIN, 3, self.footer_text)
            if self.sig_name and self.sig_title:
                fx = right_x
                self.set_xy(fx, extra_y)
                self.set_font('Comfortaa', '', 7)
                self.cell(A4_W / 2 - MARGIN, 3, 'Authorized by', align='R', new_x='LMARGIN', new_y='NEXT')
                self.set_x(fx)
                self.set_font('Comfortaa', 'B', 7)
                self.cell(A4_W / 2 - MARGIN, 3, self.sig_name, align='R', new_x='LMARGIN', new_y='NEXT')
                self.set_x(fx)
                self.set_font('Comfortaa', '', 6)
                self.cell(A4_W / 2 - MARGIN, 3, self.sig_title, align='R', new_x='LMARGIN', new_y='NEXT')

    def render(self):
        self.add_page()
        inv = self.invoice
        company = self.company

        pri_rgb = self.hex_to_rgb(self.pri)
        sec_rgb = self.hex_to_rgb(self.sec)
        acc_rgb = self.hex_to_rgb(self.acc)

        self.render_header_zone(inv, company, pri_rgb, sec_rgb)
        self.render_body(inv, company, pri_rgb, sec_rgb, acc_rgb)
        return self


def generate_invoice_pdf(invoice, company):
    pdf = InvoicePDF(invoice, company)
    pdf.render()
    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf
