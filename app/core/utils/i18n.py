"""Dual-language presentation.

The web app shows every interface text in Arabic together with English or
French. Two language pairs are supported and the user picks one from the
Account menu:

    ``ar-en``  Arabic + English   (default)
    ``ar-fr``  Arabic + French

``dual(key)`` renders a key as a bilingual fragment::

    <span class="dual"><span class="d-p" lang="en">Orders</span>
                       <span class="d-s" lang="ar">الطلبات</span></span>

The layout of that fragment (side by side, stacked, two columns, three
columns) is decided in CSS from the surrounding element, so templates only
ever call ``dual('Key')``.

A key without an Arabic translation renders once instead of repeating the
English text twice.
"""

from markupsafe import Markup, escape

from app.translations import _

# Cookie name and the pairs the Account menu offers.
PAIR_COOKIE = 'lang_pair'
DEFAULT_PAIR = 'ar-en'

LANG_PAIRS = {
    'ar-en': 'en',
    'ar-fr': 'fr',
}

PAIR_LABELS = {
    'ar-en': 'العربية / English',
    'ar-fr': 'العربية / Français',
}

# Short badge shown next to the active pair in the menu.
PAIR_BADGES = {
    'ar-en': 'AR / EN',
    'ar-fr': 'AR / FR',
}


def resolve_pair(value):
    """Normalise a cookie value into a supported pair code."""
    return value if value in LANG_PAIRS else DEFAULT_PAIR


def primary_lang(pair):
    """The non-Arabic language of the pair: ``en`` or ``fr``."""
    return LANG_PAIRS[resolve_pair(pair)]


def arabic(key):
    """Arabic text for ``key`` (falls back to the key itself)."""
    return _(key, 'ar')


def dual_markup(key, primary='en'):
    """Render ``key`` as a bilingual fragment safe to embed in HTML."""
    text_primary = _(key, primary)
    text_arabic = _(key, 'ar')

    # No Arabic translation: show the primary language once rather than
    # printing the same English sentence twice.
    if text_arabic == key:
        return Markup(
            '<span class="dual"><span class="d-p" lang="%s">%s</span></span>'
            % (escape(primary), escape(text_primary))
        )

    return Markup(
        '<span class="dual">'
        '<span class="d-p" lang="%s">%s</span>'
        '<span class="d-s" lang="ar" dir="rtl">%s</span>'
        '</span>' % (escape(primary), escape(text_primary), escape(text_arabic))
    )
