import bleach


def sanitize_html(text):
    return bleach.clean(text, tags=[], strip=True)


def paginate(page, per_page):
    try:
        page = max(int(page), 1)
    except (ValueError, TypeError):
        page = 1
    try:
        per_page = min(max(int(per_page), 1), 100)
    except (ValueError, TypeError):
        per_page = 20
    return page, per_page
