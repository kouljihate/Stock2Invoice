"""One-shot refactor: blueprint _company_id()/_get_user() now delegate to
app.core.utils.context so tenant scope and identity come from the database
instead of JWT claims. Run from the project root; prints what it changed."""
import re
from pathlib import Path

FILES = [
    'app/blueprints/eshop/routes.py',
    'app/blueprints/mobile/dashboard/routes.py',
    'app/blueprints/mobile/invoices/routes.py',
    'app/blueprints/mobile/orders/routes.py',
    'app/blueprints/mobile/stock/routes.py',
    'app/blueprints/web/customers/routes.py',
    'app/blueprints/web/customer_quotes/routes.py',
    'app/blueprints/web/dashboard/routes.py',
    'app/blueprints/web/delivery_notes/routes.py',
    'app/blueprints/web/events/routes.py',
    'app/blueprints/web/goods_receipt/routes.py',
    'app/blueprints/web/invoices/routes.py',
    'app/blueprints/web/orders/routes.py',
    'app/blueprints/web/payments/routes.py',
    'app/blueprints/web/purchase_orders/routes.py',
    'app/blueprints/web/stock/routes.py',
    'app/blueprints/web/suppliers/routes.py',
    'app/blueprints/web/supplier_invoices/routes.py',
    'app/blueprints/web/users/routes.py',
    'app/blueprints/admin/routes.py',
]

CID_NEW = (
    'def _company_id():\n'
    '    """Acting user\'s company id, resolved from the database (never claims)."""\n'
    '    from app.core.utils.context import current_company_id\n'
    '    return current_company_id()\n'
)

USER_NEW = (
    'def _get_user():\n'
    '    """Acting user document, resolved from the database (never claims)."""\n'
    '    from app.core.utils.context import current_user\n'
    '    return current_user()\n'
)

FUNC_RE = r'def _company_id\(\):\n(?:[ \t]+[^\n]*\n)+'
FUNC_USER_RE = r'def _get_user\(\):\n(?:[ \t]+[^\n]*\n)+'

changed = 0
for rel in FILES:
    path = Path(rel)
    text = path.read_text(encoding='utf-8')
    orig = text
    n_cid = len(re.findall(FUNC_RE, text))
    n_user = len(re.findall(FUNC_USER_RE, text))
    text = re.sub(FUNC_RE, CID_NEW, text)
    text = re.sub(FUNC_USER_RE, USER_NEW, text)

    # Drop now-unused get_jwt imports (keep get_jwt_identity, jwt_required, ...)
    if 'get_jwt()' not in text:
        def _strip(m):
            names = [n.strip() for n in m.group(1).split(',') if n.strip() != 'get_jwt']
            return 'from flask_jwt_extended import ' + ', '.join(names)
        text = re.sub(r'from flask_jwt_extended import ([^\n]+)', _strip, text)

    if text != orig:
        path.write_text(text, encoding='utf-8')
        changed += 1
        print(f'{rel}: _company_id={n_cid} _get_user={n_user}')

print(f'files changed: {changed}')
