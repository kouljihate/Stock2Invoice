# Font Files

## Arabic — VIP Rawy (default Arabic typeface)

| File | Weight | Used for |
|---|---|---|
| `VIP-Rawy-Regular.ttf` | 400 | body text |
| `VIP-Rawy-Bold.ttf` | 700 | headings, emphasis |
| `VIP-RAWY-THIN.ttf` | 300 | light headings |

All three are registered in `app/static/css/main.css` as the single family
`'VIP Rawy'` and exposed as the CSS variable `--font-arabic`.

The `unicode-range` on each face deliberately **excludes digits**
(`U+0030-0039`, `U+0660-0669`) so numerals keep rendering in Comfortaa, which
matches the rest of the interface.

Arabic text picks up VIP Rawy automatically:

- `<span lang="ar">` / `.d-s` — every Arabic half of a `dual()` label
- `[dir="rtl"]` containers
- any other Arabic glyph, because `--font-default` lists `'VIP Rawy'` right
  after `'Comfortaa'` and font fallback is resolved per glyph

## Latin — Comfortaa

`Comfortaa-Regular.ttf`, `Comfortaa-Light.ttf`, `Comfortaa-Bold.ttf` and
`Comfortaa-Variable.ttf` back `--font-default` (English) and `--font-french`
(French). The Google Fonts copy loaded in `base/layout.html` takes precedence
when the CDN is reachable; these files are the offline equivalents.

## Icons

`uicons-*` files back `uicons.css` (Flaticon icons used by the themes).
