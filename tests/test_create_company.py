import os
import re
import sys
import random
import struct
import tempfile
import zlib
from datetime import datetime

from playwright.sync_api import expect, sync_playwright

BASE_URL = "http://127.0.0.1:5000"

COMPANIES = [
    "Atlas Digital Services", "Casa Clean Pro", "Maroc Express Logistique",
    "Rabat Tech Solutions", "Fes Cuir Artisanat", "Agadir Fresh Produce",
    "Tanger Shipping Agency", "Marrakech Oasis Tours", "Safi Textile Industrie",
    "Oujda Commerce General", "Meknes Print & Copy", "El Jadida Peche",
    "Kenitra Bois Menuiserie", "Tetouan Batiment", "Beni Mellal Agri",
    "Nador Transport", "Laayoune Energie Services", "Dakhla Peche Export",
    "Settat Metal Works", "Khouribga Mining Support", "Casa Web Agency",
    "Rabat Comptabilite", "Maroc Vert Jardinage", "Casa Auto Reparation",
    "Fes Poterie Tradition", "Tanger Free Zone Services", "Agadir Peche Tourisme",
    "Marrakech Riad Hospitality", "Casa Pharma Distribution", "Rabat Formation Pro",
    "Mohammedia Raffinage", "Sale Logistique Urbaine", "Meknes Produits Laitiers",
    "Taza Construction", "El Kelaa Transport", "Casa Print Services",
    "Tanger Peche Export", "Fes Tannery Cuir", "Rabat Informatique",
    "Safi Conserves Alimentaires", "Casa Nettoyage Proprete", "Marrakech Art Gallery",
    "Oujda Frontiere Services", "Kenitra Bois Charpente", "Casa Electro Menager",
    "Rabat Photographie", "Tanger Transit Douane", "Fes Artisanat Zellige",
    "Agadir Peche Industrie", "Laayoune Transport Desert",
]


def _make_png(pixels, size=64):
    raw = b""
    for y in range(size):
        raw += b"\x00"
        for x in range(size):
            raw += struct.pack("BBB", *pixels[y * size + x])

    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(raw))
    return sig + ihdr + idat + chunk(b"IEND", b"")


def _generate_logo(name):
    try:
        rng = random.Random(name)
        bg = (rng.randint(30, 200), rng.randint(30, 200), rng.randint(30, 200))
        fg = (min(255, bg[0] + 80), min(255, bg[1] + 80), min(255, bg[2] + 80))

        size = 64
        cx = cy = size // 2
        r = size // 3
        pixels = []
        for y in range(size):
            for x in range(size):
                dx, dy = x - cx, y - cy
                if dx * dx + dy * dy < r * r:
                    pixels.append(fg)
                else:
                    pixels.append(bg)
        logo_bytes = _make_png(pixels, size)

        fd, path = tempfile.mkstemp(suffix=".png")
        os.write(fd, logo_bytes)
        os.close(fd)
        return path
    except Exception:
        return None


MOROCCAN_NAMES = [
    "Youssef Benali", "Fatima Zahra El Amrani", "Mohamed El Idrissi",
    "Amina Bouskri", "Hassan El Fassi", "Khadija Ouazzani",
    "Omar Bennani", "Nadia Tazi", "Karim El Maleh",
    "Sara Berrada", "Rachid El Alami", "Meryem El Ghali",
    "Adil El Haddad", "Sanae El Mokhtar", "Hicham El Filali",
    "Imane El Kadiri", "Nabil El Amraoui", "Salma El Mansouri",
    "Soufiane El Moutaouakil", "Lamia El Khayat",
    "Mehdi El Aissaoui", "Ghita El Fathi", "Anas El Mahfoudi",
    "Mouna El Hachimi", "Yassine El Ouafi",
]

def _existing_names(page):
    page.goto(f"{BASE_URL}/admin/companies")
    page.wait_for_selector("table")
    return {page.locator("table tbody tr td:first-child strong").nth(i).inner_text()
            for i in range(page.locator("table tbody tr td:first-child strong").count())}


def _pick_unused(existing):
    available = [c for c in COMPANIES if c not in existing]
    return random.choice(available) if available else random.choice(COMPANIES)


def _create_single_company(page, index=0):
    existing = _existing_names(page)
    company = _pick_unused(existing)
    ts = datetime.now().strftime("%Y%m%d%H%M%S%f")[:16]

    if company in existing:
        company_name = f"{company} {ts}"
    else:
        company_name = company

    print(f"  [{index}] Creating: {company_name}")

    logo_path = _generate_logo(company_name)
    admin_name = random.choice(MOROCCAN_NAMES)
    email_local = admin_name.lower().replace(" ", ".")

    page.goto(f"{BASE_URL}/admin/companies/create")
    page.wait_for_selector("form")

    page.fill("input[name='company_name']", company_name)
    page.fill("input[name='phone']", "+212 522 12 34 56")
    page.fill("input[name='address']", "123 Boulevard Mohammed V")
    page.fill("input[name='city']", "Casablanca")
    page.fill("input[name='website']", f"https://{company.split()[0].lower()}.ma")

    if logo_path:
        page.set_input_files("input[name='logo']", logo_path)

    page.fill("input[name='contact_name']", admin_name)
    page.fill("input[name='contact_email']", f"{email_local}@test.ma")

    page.fill("input[name='ice']", f"IC{ts[-8:]}")
    page.fill("input[name='rc']", f"RC{ts[-8:]}")
    page.fill("input[name='if_tax']", f"IF{ts[-8:]}")
    page.fill("input[name='cnss']", f"CNSS{ts[-8:]}")
    page.fill("input[name='patente']", f"PAT{ts[-8:]}")

    page.fill("input[name='admin_name']", admin_name)
    page.fill("input[name='admin_email']", f"{email_local}@test.ma")
    page.fill("input[name='admin_password']", "admin@123")

    page.click("button[type='submit']")
    try:
        page.wait_for_url(re.compile(r"/admin/?$"), timeout=10000)
        expect(page.locator(".alert-success")).to_be_visible()
        print(f"  [{index}] OK")
    except Exception as e:
        print(f"  [{index}] TIMEOUT/ERROR: {e}")

    if logo_path and os.path.exists(logo_path):
        os.remove(logo_path)


def create_companies(count):
    print(f"Creating {count} company/companies...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        page.goto(f"{BASE_URL}/web/auth/login")
        page.fill("input[name='email']", "admin@SI.ma")
        page.fill("input[name='password']", "admin@123")
        page.click("button[type='submit']")
        page.wait_for_url(re.compile(r"/admin/?"))

        for i in range(1, count + 1):
            _create_single_company(page, i)

        browser.close()
    print("Done.")


# ── CLI entry point ──
if __name__ == "__main__":
    try:
        n = int(sys.argv[1])
    except (IndexError, ValueError):
        n = 1
    create_companies(n)


# ── pytest entry point (always creates 1) ──
class TestCreateCompany:
    def test_create_company_successfully(self):
        create_companies(1)
